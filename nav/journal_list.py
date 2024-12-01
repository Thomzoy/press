from bs4 import BeautifulSoup
import json
from .login import setup_headless_browser

import time
import pandas as pd

JOURNAL_PATH = "journals.csv"
JOURNAL_URL = "https://nouveau-europresse-com.bnf.idm.oclc.org/Pdf/GetInitialResults"

def get_journals(
    driver=None,
    search_results_url=JOURNAL_URL,
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
        all_data.extend(
            list(data["SortedSources"].values())
        )
    
    df = pd.DataFrame(all_data)
    df.to_csv(JOURNAL_PATH, index=False)
    return df
