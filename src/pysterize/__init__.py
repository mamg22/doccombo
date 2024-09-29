import argparse
import itertools
from functools import reduce
import operator
from pathlib import Path

import pymupdf as pm  # type: ignore


LETTER_PAPER = pm.paper_rect("letter")

# Letter paper size
AREA_TEMPLATE = (
    pm.Rect(10, 13, 301, 233),
    pm.Rect(314, 13, 601, 233),
    pm.Rect(10, 246, 301, 454),
    pm.Rect(314, 246, 601, 454),
    pm.Rect(10, 465, 202, 769),
    pm.Rect(212, 465, 400, 769),
    pm.Rect(409, 465, 601, 770),
)


def load_files(directory: Path) -> list[pm.Document]:
    files = []

    for file in directory.iterdir():
        if file.is_dir():
            continue
        else:
            doc = pm.open(file)
            if not doc.is_pdf:
                pdf_bytes = doc.convert_to_pdf()
                doc = pm.open(stream=pdf_bytes)
            files.append(doc)

    return files


def draw_box(page: pm.Page, rect: pm.Rect, color: tuple[float, float, float]) -> None:
    "Utility function to easily draw a rectangle for debugging purposes, mostly in crop_page()"
    shape = page.new_shape()
    shape.draw_rect(rect)
    shape.finish(color=color)
    shape.commit()


def crop_page(page: pm.Page) -> bool:
    if page.rotation != 0:
        page.remove_rotation()

    rects = []
    for draw in page.get_drawings():
        rect = draw["rect"]
        if rect.get_area() < 500:
            continue
        match draw:
            case (
                {"color": (1, 1, 1), "fill": None}
                | {"color": None, "fill": (1, 1, 1)}
            ):
                continue

        rects.append(rect)

    for text in page.get_text("blocks"):
        rect = pm.Rect(text[:4])
        if text[4].isspace():
            continue
        rects.append(rect)

    for image in page.get_image_info():
        rect = pm.Rect(image["bbox"])
        rects.append(rect)

    # Page is empty, no noticeable elements found
    if not rects:
        return False

    # Limit found rects to page bounds.
    full = reduce(operator.or_, rects) & page.mediabox

    page.set_cropbox(full)

    return True


def parse_commandline() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Combine documents and images in a directory into a single PDF"
    )
    parser.add_argument(
        "directory",
        help="Directory where the files to combine are located",
        type=Path,
    )
    parser.add_argument(
        "output_file",
        help="Output filename (Default: `%(default)s`)",
        default="out.pdf",
        nargs="?",
        type=Path,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_commandline()

    files = load_files(args.directory)

    output_doc = pm.Document()

    slot_iter = itertools.cycle(range(len(AREA_TEMPLATE)))
    page_iter = filter(crop_page, itertools.chain.from_iterable(files))

    # Iterate on (template_slot, page) pairs.
    # The chain will extract all pages from each document
    for slot, page in zip(slot_iter, page_iter):
        if slot == 0:
            curr_page = output_doc.new_page(
                width=LETTER_PAPER.width, height=LETTER_PAPER.height
            )
        else:
            curr_page = output_doc[-1]

        area = AREA_TEMPLATE[slot]
        area_vert = area.height > area.width
        page_vert = page.rect.height > page.rect.width

        if area_vert ^ page_vert:
            rotate = 90
        else:
            rotate = 0

        curr_page.show_pdf_page(area, page.parent, page.number, rotate=rotate)

    output_doc.ez_save(args.output_file)


if __name__ == "__main__":
    main()
