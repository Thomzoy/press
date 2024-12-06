import json
from pathlib import Path
import os
import base64

from nav.login import login_and_navigate
from nav.img import Images
from nav.pdf import PDF
from nav.google import Google
from nav.journals import JOURNALS_FOLDER_ID

LOGIN_URL = "https://authentification.bnf.fr/login"
LANDING_PAGE_URL = "https://bnf.idm.oclc.org/login?url=https://nouveau.europresse.com/access/ip/default.aspx?un=D000067U_1&sa=D&sntz=1&usg=AOvVaw359KkJUvjTjlJuRfT-OlnE"
TARGET_PAGES = [LANDING_PAGE_URL]

journals_path = Path.cwd().resolve() / "journals"
journals_path.mkdir(parents=True, exist_ok=True)


def get_tokens():
    BNF_USER = os.environ.get("BNF_USER", None)
    BNF_TOKEN = os.environ.get("BNF_TOKEN", None)
    B64_DRIVE_TOKEN = os.environ.get("B64_DRIVE_TOKEN", None)
    if B64_DRIVE_TOKEN is None:
        creds_path = Path("./credentials.json")
        if creds_path.exists():
            DRIVE_TOKEN = creds_path.read_text()
        else:
            raise ValueError("No Google Drive token found")
        DRIVE_TOKEN = json.loads(DRIVE_TOKEN)
    else:
        DRIVE_TOKEN = json.loads(base64.b64decode(B64_DRIVE_TOKEN))

    return BNF_USER, BNF_TOKEN, DRIVE_TOKEN


def get_journal():
    BNF_USER, BNF_TOKEN, DRIVE_TOKEN = get_tokens()

    for journal_id in JOURNALS_FOLDER_ID.keys():
        print(f"Getting journal {journal_id}")
        driver = login_and_navigate(
            LOGIN_URL,
            BNF_USER,
            BNF_TOKEN,
            TARGET_PAGES,
        )
        try:
            google = Google(
                journal_id=journal_id,
                credentials=DRIVE_TOKEN,
            )
            existing_dates = google.get_existing_journal_dates()

            images = Images(
                driver=driver,
                journal_id=journal_id,
                wait_time=30,
                limit=-1,
                do_screenshot=True,
                overwrite=False,
                existing_dates=existing_dates,
            )
            result = images.run(n_try=4)
            if result == "skip":
                print(f"Edition {images.date} of {journal_id} already saved !")
                continue
            elif result == "miss":
                raise ValueError("Could not save everything !")
            else:
                print("All good!")
            pdf = PDF(
                pngs_path=images.images_path,
                output_path=images.images_path / f"{images.date}.pdf",
            )
            pdf.run()
            file = google.run(
                pdf_path=pdf.output_path,
            )
            print(file["webViewLink"])
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            driver.close()
            driver.quit()


if __name__ == "__main__":
    get_journal()
