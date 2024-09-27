import itertools
from pathlib import Path
import sys

import pymupdf as pm  # type:ignore


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


def main():
    try:
        target_dir = Path(sys.argv[1])
    except IndexError:
        target_dir = Path.cwd()

    files = load_files(target_dir)

    output_doc = pm.Document()

    # Iterate on (template_slot, page) pairs.
    # The chain will extract all pages from each document
    for slot, page in zip(
        itertools.cycle(range(len(AREA_TEMPLATE))),
        itertools.chain.from_iterable(files),
    ):
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

    output_doc.ez_save("out.pdf")


if __name__ == "__main__":
    main()
