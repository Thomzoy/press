from collections import defaultdict

from bs4 import BeautifulSoup
import json

import pandas as pd

# MD_P : Le monde diplo
# IL_P : courrier international
# HU_P : humanité

JOURNAL_PATH = "journals.csv"
JOURNAL_SEARCH_URL = (
    "https://nouveau-europresse-com.bnf.idm.oclc.org/Pdf/GetInitialResults"
)
JOURNAL_URL = "https://nouveau-europresse-com.bnf.idm.oclc.org/Pdf/Edition?sourceCode={journal_id}"
JOURNALS_FOLDER_ID = defaultdict(
    lambda: "1cX0ZYAPCH5QMPzjwNiDdo6jijRRL5_MY",
    LM_P="1U7WvK7krTk_szGl62hqoJmdhYBe-Mm0Z",
    LI_P="1qSnTfziuScpDOKoCEkZLZLwAPc9QqRAY",
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
