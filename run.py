import json
from pathlib import Path
import os
import base64
import traceback
from datetime import datetime
import warnings
from github import Github

# import chromedriver_autoinstaller

from nav.login import login_and_navigate
from nav.img import Images
from nav.pdf import PDF
# from nav.google import Google
from nav.journals import JOURNALS_FOLDER_ID
from html_index import create_index_html
from index import generate_index
from loan import get_all

LOGIN_URL = "https://authentification.bnf.fr/login"
LANDING_PAGE_URL = "https://bnf.idm.oclc.org/login?url=https://nouveau.europresse.com/access/ip/default.aspx?un=D000067U_1&sa=D&sntz=1&usg=AOvVaw359KkJUvjTjlJuRfT-OlnE"
TARGET_PAGES = [LANDING_PAGE_URL]

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


def get_all_editions(delete_days_threshold: int = 7, dry: bool = False):
    all_editions = dict()

    GH_TOKEN = os.environ.get("GH_TOKEN", None)
    g = Github(GH_TOKEN)
    repo = g.get_repo("Thomzoy/press")
    contents = repo.get_contents("Journaux", ref="gh-pages")

    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path, ref="gh-pages"))
        elif file_content.type == "file":
            try:
                date = datetime.strptime(Path(file_content.path).parent.name, "%Y-%m-%d")
                journal_name = Path(file_content.path).parent.parent.name
                all_editions[journal_name] = all_editions.get(journal_name, dict())
                date_str = date.strftime("%Y-%m-%d")
                all_editions[journal_name][date_str] = all_editions[journal_name].get(date_str, [])
                all_editions[journal_name][date_str].append(
                    str(Path(file_content.path).relative_to("Journaux/"))
                )
                delta = (datetime.now() - date).days
                if (delete_days_threshold>0) and delta >= delete_days_threshold:
                    print("Deleting: ", file_content.path)
                    if not dry:
                        repo.delete_file(
                            path=file_content.path,
                            message=f"Delete {file_content.path}",
                            sha=file_content.sha,
                            branch="gh-pages"
                        )
            except Exception as e:
                print(e)

    print("Existing journals: ", all_editions)
    return all_editions


def get_journal():

    existing_dates = get_all_editions(delete_days_threshold=7) # TODO: Change to 7
    BNF_USER, BNF_TOKEN, ILOVEPDF_PUBLIC_KEY = get_tokens()

    driver = login_and_navigate(
        LOGIN_URL,
        BNF_USER,
        BNF_TOKEN,
        TARGET_PAGES,
    )
    print("Done")

    GH_TOKEN = os.environ.get("GH_TOKEN", None)
    g = Github(GH_TOKEN)
    repo = g.get_repo("Thomzoy/press")
    base = Path("./Journaux/")

    for journal_id, journal_name in JOURNALS_FOLDER_ID.items():
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
                existing_dates=list(existing_dates.get(journal_name, dict()).keys()),
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
            final_folder = pdf.optimize_pdf(output_path=output_path, max_size=39)
        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()
        finally:
            driver.close()
            driver.quit()

def upload_journal():

    GH_TOKEN = os.environ.get("GH_TOKEN", None)
    g = Github(GH_TOKEN)
    repo = g.get_repo("Thomzoy/press")
    base = Path("./Journaux/")
    for path in base.glob("**/*"):
        if path.is_file():
            content = path.read_bytes()
            try:
                if path.name.endswith("pdf"):
                    remote_path = str(path)
                    print(f"Upload {remote_path}")
                    repo.create_file(
                        remote_path,
                        message=f"Upload {remote_path}",
                        content=content,
                        branch="gh-pages"
                    )
            except Exception as e:
                print(e)

def upload_index():

    GH_TOKEN = os.environ.get("GH_TOKEN", None)
    g = Github(GH_TOKEN)
    repo = g.get_repo("Thomzoy/press")
    path = Path("./Journaux/index.html")
    try:
        remote_content = repo.get_contents(str(path), ref="gh-pages")
        repo.update_file(
            remote_content.path, 
            message="Update index.html",
            content=path.read_bytes(), 
            sha=remote_content.sha,
            branch="gh-pages",
        )
    except Exception as e:
        print(e)

if __name__ == "__main__":
    get_journal()
    upload_journal()
    existing = get_all_editions(-1, dry=True)
    generate_index(existing)
    upload_index()
    #create_index_html()
    #get_all("./esketit")
