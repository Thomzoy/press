import pymupdf
from pylovepdf.ilovepdf import ILovePdf
from pathlib import Path
from tqdm import tqdm
import shutil
import os 


class PDF:
    def __init__(
        self,
        public_key,
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
        self.public_key = public_key

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
            shutil.rmtree(image.parent)

        print("Saving...")
        doc.save(self.output_path)
        print(f"Saved to {self.output_path}")


    def get_mb_size(self, path):
        return path.stat().st_size / 1e6

    def get_pdfs_names(self, folder_path):
        return [path.name for path in folder_path.glob("*")]

    def optimize_pdf(self, output_path=None, max_size=49):

        path = self.output_path # Initial PDF path
        name = path.name
        stem = path.stem
        final_folder = output_path
        if output_path is None:
            final_folder = path.parent / stem
        final_folder.mkdir(exist_ok=True)

        destination = final_folder / "1.pdf"

        shutil.move(path, destination) # TODO change to move

        path = destination

        size_mb = self.get_mb_size(path)
        if size_mb <= max_size:
            print("Case 1 - No compression needed: ", self.get_pdfs_names(final_folder))
            return final_folder
        
        print(f"Case 2 - Compression needed ({size_mb})")

        ilovepdf = ILovePdf(self.public_key, verify_ssl=True)

        # Compress
        task = ilovepdf.new_task('compress')
        task.add_file(path)
        task.set_output_folder(final_folder)
        task.execute()
        task.download(filename="compressed.pdf")
        task.delete_current_task()

        compressed_file = final_folder / "compressed.pdf"
        shutil.move(compressed_file, compressed_file.with_name("1.pdf"))

        size_mb = self.get_mb_size(path)
        if size_mb <= max_size:
            print(f"Case 2 done - Compressed PDF size {size_mb}Mb < f{max_size}Mb: ", self.get_pdfs_names(final_folder))
            return final_folder
        
        size_mb = self.get_mb_size(path)
        n_splits = int(1 + size_mb // max_size)
        print(f"Case 3 - Compressed PDF size {size_mb}Mb > f{max_size}Mb, splitting in {n_splits} files")

        doc = pymupdf.open(path)
        page_count = doc.page_count
        fixed_range = int( page_count // n_splits)

        task = ilovepdf.new_task('split')
        task.add_file(path)
        task.set_output_folder(final_folder)
        task.split_mode = "fixed_range"
        task.fixed_range = str(fixed_range)
        task.execute()
        task.download(filename="splitted.zip")
        task.delete_current_task()

        archive_path = final_folder / "splitted.zip"
        shutil.unpack_archive(archive_path, final_folder)
        archive_path.unlink()
        path.unlink()

        paths = sorted(Path(final_folder).glob("*.pdf"), key=lambda path:path.name)
        for idx, path in enumerate(paths):
            shutil.move(path, path.with_stem(str(idx+1)))

        print("Case 3 done - Compressed and splitted: ", self.get_pdfs_names(final_folder))
        return final_folder

