from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import NoReturn

import click
import fitz

__version__ = "0.0.3"


def format_width(n: int) -> int:
    return len(str(n))


def fail(e: Exception) -> NoReturn:
    ctx = click.get_current_context()
    ctx.fail(str(e))


@click.command()
@click.argument("file", nargs=-1, type=click.Path(exists=True))
@click.option("-o", "--out", type=click.Path(), default=None, help="Output directory, defaulting <CWD>.")
@click.version_option(__version__)
def main(file: Iterable[Path], out: None | str = None):
    """Extract images from pdf"""
    # print help if no file given
    if not file:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit()

    out_dir = Path.cwd() if out is None else Path(out)

    for src in map(Path, file):
        try:
            fitz_doc = fitz.open(src, filetype="pdf")
        except Exception as e:  # noqa: BLE001
            fail(e)

        click.echo(f"✅ found {src}")

        dst = out_dir / src.stem
        # make empty dist dir, even the pdf contains no images
        try:
            dst.mkdir(parents=True, exist_ok=True)
        except Exception as e:  # noqa: BLE001
            fail(e)

        total_images = 0

        total_pages = len(fitz_doc)
        page_width = format_width(total_pages)

        for page_no, fitz_page in enumerate(fitz_doc):
            images = fitz_page.get_images()

            image_no = len(images)
            image_width = format_width(image_no)

            total_images += image_no

            # FIXME: should use get_image_info(xref=True)?
            for img_no, img in enumerate(images):
                xref = img[0]

                if (image := fitz_doc.extract_image(xref)) is None:
                    continue

                ext = image["ext"]
                data = image["image"]

                folder = dst / f"{page_no:0{page_width}}"
                # make page dir, only if the page contains image
                try:
                    folder.mkdir(parents=True, exist_ok=True)
                except Exception as e:  # noqa: BLE001
                    fail(e)

                name = folder / f"{img_no:0{image_width}}.{ext}"

                try:
                    name.write_bytes(data)
                except Exception as e:  # noqa: BLE001
                    fail(e)

        pages = "pages" if total_pages > 1 else "page"
        images = "images" if total_images > 1 else "image"
        click.echo(f"✨ extract {total_images} {images} from {total_pages} {pages}")


if __name__ == "__main__":
    main()
