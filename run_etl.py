import json

import pandas as pd
from tqdm import tqdm

from src.models.request import BasicBusinessInfo, RunETLRequest

if __name__ == "__main__":
    df = pd.read_csv("./data/locations.csv")
    businesses = [
        BasicBusinessInfo(
            location_name=row["name"] if pd.notna(row["name"]) else None,
            phone_number=row["phone"] if pd.notna(row["phone"]) else None,
            zip_code=row["zip_code"] if pd.notna(row["zip_code"]) else None,
        )
        for row in tqdm(df.to_dict("records"), desc="Processing businesses")
    ]
    request = RunETLRequest(businesses=businesses)

    with open("locations.json", "w") as f:
        json.dump(locations, f)
