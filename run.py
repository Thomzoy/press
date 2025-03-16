import json
from pathlib import Path
import os
import base64
import traceback
import fsspec
import requests
from datetime import datetime
import warnings
import shutil

# import chromedriver_autoinstaller

from nav.login import login_and_navigate
from nav.img import Images
from nav.pdf import PDF
from nav.google import Google
from nav.journals import JOURNALS_FOLDER_ID
from html_index import create_index_html
from loan import get_all

LOGIN_URL = "https://authentification.bnf.fr/login"
LANDING_PAGE_URL = "https://bnf.idm.oclc.org/login?url=https://nouveau.europresse.com/access/ip/default.aspx?un=D000067U_1&sa=D&sntz=1&usg=AOvVaw359KkJUvjTjlJuRfT-OlnE"
TARGET_PAGES = [LANDING_PAGE_URL]

os.environ["BNF_USER"] = "thom.petitjean@hotmail.fr"
os.environ["BNF_TOKEN"] = "Presse écrite BNF 2024"


def get_tokens():
    BNF_USER = os.environ.get("BNF_USER", None)
    BNF_TOKEN = os.environ.get("BNF_TOKEN", None)
    ILOVEPDF_PUBLIC_KEY = os.environ.get("ILOVEPDF_PUBLIC_KEY", None)

    return BNF_USER, BNF_TOKEN, ILOVEPDF_PUBLIC_KEY
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


def get_all_editions(delete_days_threshold: int = 7):
    r = requests.get("https://api.github.com/repos/Thomzoy/press/git/refs/heads/gh-pages")
    sha = r.json()["object"]["sha"]

    all_editions = dict()
    for journal_name in JOURNALS_FOLDER_ID.values():
        editions = []
        destination = Path("./Journaux") / journal_name
        destination.mkdir(exist_ok=True, parents=True)
        fs = fsspec.filesystem("github", org="Thomzoy", repo="press", sha=sha)
        try:
            fs.get(fs.ls(f"Journaux/{journal_name}"), destination.as_posix(), recursive=False)
        except FileNotFoundError:
            print(f"Journal {journal_name} not found in GH-Pages")

        for path in destination.glob("./*"):
            if path.is_dir():
                fs.get(fs.ls(f"Journaux/{journal_name}/{path.name}"), path.as_posix(), recursive=False)
            date_str = path.stem
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
                if (delete_days_threshold>0) and (datetime.now() - date).days >= delete_days_threshold:
                    print(date, (datetime.now() - date))
                    shutil.rmtree(path)
                editions.append(date.strftime("%Y-%m-%d"))
            except Exception as e:
                print("Date parse error: ", str(e))
        all_editions[journal_name] = editions
    return all_editions


def get_journal():

    existing_dates = get_all_editions()
    BNF_USER, BNF_TOKEN, ILOVEPDF_PUBLIC_KEY = get_tokens()

    driver = login_and_navigate(
        LOGIN_URL,
        BNF_USER,
        BNF_TOKEN,
        TARGET_PAGES,
    )
    print("Done")
    for journal_id in JOURNALS_FOLDER_ID.keys():
        print(f"Getting journal {journal_id}")
        if not driver.service.is_connectable():
            print("Reconnecting driver...")
            driver = login_and_navigate(
                LOGIN_URL,
                BNF_USER,
                BNF_TOKEN,
                TARGET_PAGES,
            )
            print("Done")

        try:

            images = Images(
                driver=driver,
                journal_id=journal_id,
                wait_time=30,
                limit=-1,
                do_screenshot=False,
                overwrite=False,
                existing_dates=existing_dates.get(journal_id, []),
            )
            result = images.run(n_try=4)
            if result == "skip":
                print(f"Edition {images.date} of {journal_id} already saved !")
                continue
            elif result == "miss":
                warnings.warn("Could not save all pages !")
            else:
                print("All good!")
            output_path=images.images_path.parent.parent / images.date
            output_path.mkdir(parents=True, exist_ok=True)
            pdf = PDF(
                public_key=ILOVEPDF_PUBLIC_KEY,
                images_path=images.images_path,
                output_path=output_path / "1.pdf",
            )
            pdf.run()
            pdf.optimize_pdf(output_path=output_path, max_size=39)
        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()
        finally:
            driver.close()
            driver.quit()


if __name__ == "__main__":
    get_journal()
    create_index_html()
    get_all("./esketit")