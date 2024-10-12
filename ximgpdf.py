from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

import click
import fitz

__version__ = "0.0.2"


def format_width(n: int) -> int:
    return len(str(n))


@click.command()
@click.argument("file", nargs=-1, type=click.Path(exists=True))
@click.option("-o", "--out", default=None, help="Output directory, defaulting <CWD>.")
@click.version_option(__version__)
def main(file: Iterable[Path], out: None | str = None):
    """Extract images from pdf"""

    if not file:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit()

    out_dir = Path.cwd() if out is None else Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)

    for src in map(Path, file):
        click.echo(f"✅ found {src}")

        dst = out_dir / src.stem
        dst.mkdir(parents=True, exist_ok=True)

        image_count = 0
        with fitz.open(src) as doc:
            page_no = len(doc)
            page_width = format_width(page_no)

            for i, page in enumerate(doc):
                image_no = len(page.get_images())
                image_width = format_width(image_no)

                image_count += image_no

                # FIXME: should use get_image_info(xref=True)?
                for j, img in enumerate(page.get_images()):
                    xref = img[0]

                    if (image := doc.extract_image(xref)) is None:
                        continue

                    ext = image["ext"]
                    data = image["image"]

                    folder = dst / f"{i:0{page_width}}"
                    folder.mkdir(parents=True, exist_ok=True)

                    name = folder / f"{j:0{image_width}}.{ext}"
                    name.write_bytes(data)

        pages = "pages" if page_no > 1 else "page"
        images = "images" if image_count > 1 else "image"
        click.echo(f"✨ extract {page_no} {pages} and {image_count} {images}")
