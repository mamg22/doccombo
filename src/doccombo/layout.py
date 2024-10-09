from collections.abc import Iterable
import io
import itertools
from functools import partial, reduce
import operator
from pathlib import Path
import re
from typing import IO

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


type LoadSrc = str | Path | bytes | bytearray | IO[bytes] | io.BytesIO


def load_file(source: LoadSrc, filename: str | None = None) -> pm.Document:
    try:
        doc = pm.open(source)
    except TypeError:
        doc = pm.open(stream=source, filename=filename)
    else:
        if doc.name is None:
            doc.name = filename

    if not doc.is_pdf:
        pdf_bytes = doc.convert_to_pdf()
        doc.close()
        doc = pm.open(stream=pdf_bytes)

    return doc


def draw_box(page: pm.Page, rect: pm.Rect, color: tuple[float, float, float]) -> None:
    "Utility function to easily draw a rectangle for debugging purposes, mostly in crop_page()"
    shape = page.new_shape()
    shape.draw_rect(rect)
    shape.finish(color=color)
    shape.commit()


def crop_page(page: pm.Page, config: dict) -> bool:
    if page.rotation != 0:
        page.remove_rotation()

    min_area = config["filter"]["drawing"]["min-area"]

    rects = []
    for draw in page.get_drawings():
        rect = draw["rect"]
        if rect.get_area() < min_area:
            continue
        match draw:
            case (
                {"color": (1, 1, 1), "fill": None}
                | {"color": None, "fill": (1, 1, 1)}
            ):
                continue

        rects.append(rect)

    try:
        text_filters = config["filter"]["text"]
        ignore_search = [
            re.compile(filt) for filt in text_filters.get("ignore-search", [])
        ]
    except KeyError:
        ignore_search = []

    for block in page.get_text("blocks"):
        rect, text = pm.Rect(block[:4]), block[4]
        if text.isspace():
            continue
        if any(regex.search(text) for regex in ignore_search):
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


def layout_pages(pages: Iterable[pm.Page]) -> pm.Document:
    slot_iter = itertools.cycle(range(len(AREA_TEMPLATE)))

    doc = pm.Document()

    # Iterate on (template_slot, page) pairs.
    # The chain will extract all pages from each document
    for slot, page in zip(slot_iter, pages):
        if slot == 0:
            curr_page = doc.new_page(
                width=LETTER_PAPER.width, height=LETTER_PAPER.height
            )
        else:
            curr_page = doc[-1]

        area = AREA_TEMPLATE[slot]
        area_vert = area.height > area.width
        page_vert = page.rect.height > page.rect.width

        if area_vert ^ page_vert:
            rotate = 90
        else:
            rotate = 0

        curr_page.show_pdf_page(area, page.parent, page.number, rotate=rotate)

    return doc


def crop_and_layout(
    file_srcs: Iterable[LoadSrc],
    config: dict,
    filenames: Iterable[str] | Iterable[None] = itertools.repeat(None),
) -> pm.Document:
    files = (load_file(file, name) for file, name in zip(file_srcs, filenames))

    page_iter = filter(
        partial(crop_page, config=config), itertools.chain.from_iterable(files)
    )

    doc = layout_pages(page_iter)

    return doc


def layout_from_directory(directory: Path, config: dict) -> pm.Document:
    files = (file for file in directory.iterdir() if file.is_file())

    return crop_and_layout(files, config)
