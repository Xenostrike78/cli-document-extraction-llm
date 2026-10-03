import pymupdf
from pathlib import Path

def convert_pdf_to_images(pdf_path, output_dir):
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Remove temporary page images from previous runs
    for old_file in output_dir.glob("page_*.jpg"):
        old_file.unlink()

    document = pymupdf.open(pdf_path)
    image_paths = []

    if len(document) > 0:
        page = document[0]

        pixmap = page.get_pixmap(
            matrix=pymupdf.Matrix(2, 2),
            alpha=False
        )

        image_path = output_dir / "page_1.jpg"

        pixmap.save(str(image_path))

        image_paths.append(image_path)

        print(f"    Page 1 -> {image_path}")

    document.close()

    return image_paths