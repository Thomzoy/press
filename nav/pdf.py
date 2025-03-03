import pymupdf
from pathlib import Path
from tqdm import tqdm

class PDF:
    def __init__(
        self,
        images_path,
        output_path=None,
        delete_images_when_done: bool=True,
    ):
        self.images_path = Path(images_path).resolve()
        self.delete_images_when_done = delete_images_when_done

        if output_path is None:
            output_path = images_path / "journal.pdf"
        self.output_path = Path(output_path).resolve()

        self.images = sorted(
            self.images_path.glob("*"),
            key=lambda path: int(path.stem),
        )

    def run(
        self,
    ):
        doc = pymupdf.open()  # PDF with the pictures
        for image in tqdm(self.images):
            with pymupdf.open(image) as img:
                rect = img[0].rect
                pdfbytes = img.convert_to_pdf()

            imgPDF = pymupdf.open("pdf", pdfbytes)
            page = doc.new_page(
                width=rect.width,
                height=rect.height,
            )
            page.show_pdf_page(rect, imgPDF, 0)
            if self.delete_images_when_done:
                image.unlink()

        print("Saving...")
        doc.save(self.output_path)
        print(f"Saved to {self.output_path}")
