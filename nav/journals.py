from collections import defaultdict
import json

from bs4 import BeautifulSoup
import pandas as pd

JOURNAL_PATH = "journals.csv"
JOURNAL_SEARCH_URL = (
    "https://nouveau-europresse-com.bnf.idm.oclc.org/Pdf/GetInitialResults"
)
JOURNAL_URL = "https://nouveau-europresse-com.bnf.idm.oclc.org/Pdf/Edition?sourceCode={journal_id}"
BASE_JOURNAL_DRIVE_FOLDER = "1WtI0PsYLENi3pijdLNDrSyj95AHQHDwi"
JOURNALS_FOLDER_ID = defaultdict(
    lambda: "Inconnu",
    LM_P="Le Monde",
    LI_P="Libération",
    HU_P="L'Humanité",
    #IL_P="Courrier International",
    #MD_P="Le Monde Diplomatique",
    #OB_P="Nouvel Obs",
    #SCA_P="Science&Avenir",
    #MSJ_P="Science&Vie",
)


def get_last_edition(
    journal_id,
    refresh,
):
    journals = get_journals(refresh=refresh)
    journal = journals[journals.Code == journal_id]
    n = len(journal)
    if n != 1:
        raise ValueError(f"Incorrect number of journals for {journal_id}: {n}")
    journal = journal.iloc[0]
    last_date = journal.SourceLastEdition.split("T")[0]
    return last_date


def get_journals(
    driver=None,
    search_results_url=JOURNAL_SEARCH_URL,
    refresh=False,
):
    if not refresh:
        return pd.read_csv(JOURNAL_PATH)

    driver.get(str(search_results_url))
    soup = BeautifulSoup(
        driver.page_source,
        features="html.parser",
    )

    dict_from_json = json.loads(soup.find("body").text)

    all_data = []
    for data in dict_from_json["SourceResult"]:
        all_data.extend(list(data["SortedSources"].values()))

    df = pd.DataFrame(all_data)
    df.to_csv(JOURNAL_PATH, index=False)
    return df
