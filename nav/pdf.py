import pymupdf
from pathlib import Path
from tqdm import tqdm

class PDF:
    def __init__(
        self,
        pngs_path,
        output_path=None,
    ):
        self.pngs_path = Path(pngs_path).resolve()

        if output_path is None:
            output_path = pngs_path / "journal.pdf"
        self.output_path = Path(output_path).resolve()

        self.pngs = sorted(
            self.pngs_path.glob("*.png"),
            key=lambda path: int(path.stem),
        )

    def run(
        self,
    ):
        doc = pymupdf.open()  # PDF with the pictures
        for png in tqdm(self.pngs):
            with pymupdf.open(png) as img:
                rect = img[0].rect
                pdfbytes = img.convert_to_pdf()

            imgPDF = pymupdf.open("pdf", pdfbytes)
            page = doc.new_page(
                width=rect.width,
                height=rect.height,
            )
            page.show_pdf_page(rect, imgPDF, 0)

        doc.save(self.output_path)
        print(f"Saved to {self.output_path}")
