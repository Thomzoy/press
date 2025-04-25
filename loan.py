import requests
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

def get_all(save_dir):
    results = []
    page = 1
    pageSize = 1000
    total = np.inf

    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/json;charset=UTF-8',
        'origin': 'https://esketit.com',
        'priority': 'u=1, i',
        'referer': 'https://esketit.com/investor/secondary-market',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
    }


    while (page-1)*pageSize < total:
        print(page)
        json_data = {
            'page': page,
            'pageSize': pageSize,
            'filter': {
                'products': [],
                'countries': [],
                'originators': [],
                'collectionStatuses': [],
                'currencyCode': 'EUR',
            },
        }
        response = requests.post('https://esketit.com/api/investor/public/query-secondary-market', headers=headers, json=json_data).json()
        total = response["total"]
        results.extend(response["items"])
        page += 1

    df = pd.DataFrame(results)
    today = datetime.now().strftime("%Y-%m-%d")
    df["date"] = today

    path = Path(save_dir).resolve()
    path.mkdir(parents=True, exist_ok=True)
    df.to_csv(path / f"{today}.csv", index=False)

    # all_df_path = path / "all.csv"
    # if all_df_path.exists():
    #     all_df = pd.read_csv(all_df_path)
    #     all_df = pd.concat([df, all_df])
    #     all_df.to_csv(all_df_path, index=False)
    # else:
    #     df.to_csv(all_df_path, index=False)
    return df

if __name__ == "__main__":
    try:
        df = get_all()
    except Exception as e:
        print("ERROR: ", e)
