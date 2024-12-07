from pathlib import Path
import traceback
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
from googleapiclient.errors import HttpError


from .journals import JOURNALS_FOLDER_ID


class Google:
    def __init__(
        self,
        journal_id,
        credentials,
    ):
        self.journal_id = journal_id
        journal = JOURNALS_FOLDER_ID[journal_id]
        self.drive_folder_id = journal[0]
        self.journal_name = journal[1]
        self.credentials = service_account.Credentials.from_service_account_info(
            credentials
        )

        self.service = build("drive", "v3", credentials=self.credentials)

    def run(
        self,
        pdf_path,
        pdf_name=None,
    ):
        self.pdf_path = Path(pdf_path).resolve()
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"File {self.pdf_path} not found !")
        self.pdf_name = pdf_name if pdf_name is not None else pdf_path.name

        try:
            # Prepare file metadata
            file_metadata = {
                "name": self.pdf_name,
                "parents": [self.drive_folder_id],
            }

            # Create media file upload object
            media = MediaFileUpload(self.pdf_path, resumable=True)

            # Execute file upload
            print("Uploading...")
            request = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id, webViewLink, webContentLink",
            )
            print("Done, checking...")
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"Uploaded {int(status.progress() * 100)}%")

            # Verify file details
            uploaded_file = (
                self.service.files()
                .get(
                    fileId=response["id"],
                    fields="id, name, size, mimeType, webViewLink, webContentLink",
                )
                .execute()
            )
            print("Done checking")

            return uploaded_file

        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def get_existing_journal_dates(self):
        try:
            print(f"Getting existing dates for {self.journal_name}")
            query = f"'{self.drive_folder_id}' in parents and trashed = false"
            results = (
                self.service.files().list(q=query, fields="files(id, name)").execute()
            )
            files = [file["name"].split(".pdf")[0] for file in results.get("files", [])]
            print(f"Existing: {files}")
            return files
        except HttpError as error:
            print(f"An error occurred when loading existing dates: {error}")
            traceback.print_exc()
            return []
