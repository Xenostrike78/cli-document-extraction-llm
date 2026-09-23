import pymupdf
from pathlib import Path

def convert_pdf_to_images(pdf_path, output_dir):
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    document = pymupdf.open(pdf_path)
    image_paths = []
    for page_number, page in enumerate(document, start=1):
        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
        image_path = output_dir / f"page_{page_number}.jpg"
        pixmap.save(str(image_path))
        image_paths.append(image_path)
        print(f"    Page {page_number} -> {image_path}")
    document.close()
    return image_paths
