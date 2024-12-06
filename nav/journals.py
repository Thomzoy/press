from collections import defaultdict
import json

from bs4 import BeautifulSoup
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
    LM_P="1U7WvK7krTk_szGl62hqoJmdhYBe-Mm0Z", # Le Monde
    LI_P="1qSnTfziuScpDOKoCEkZLZLwAPc9QqRAY", # Libé
    HU_P="1H1IHeNS15_WjDLN9iUL2lrx5WJ99TAxm", # L'Huma
    IL_P="1b-ueLbMw8mJl3FhXi4Zjw-WFtxje6r5j", # Courrier Inter.
    MD_P="1hnzXVVyPnCSZdE3uR14P2cSXwVasXZi9", # Le Monde Diplo
    OB_P="15UGAh0HR87WRANbQm9rzH8X1If6jqikw", # Nouvel Obs
    SCA_P="1hyeILhVZRPh_GduS6khT_PFB3Bco9jU9", # Science&Avenir
    MSJ_P="141zC5Hb3tT3EYaze4gQYZDjXPYZL0rnw", # Science&Vie
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
