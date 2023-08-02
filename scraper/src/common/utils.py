import re
import os
import pandas as pd

directory = os.path.dirname(os.path.realpath(__file__))

neighborhood_csv_data = pd.read_csv(f"{directory}/pc4.csv")


def get_int_from_string(text: str):
    # Regular expression pattern to find a word starting with 'q' and ending with 'k'
    pattern = r"\d+"

    # Using findall to find all occurrences of the pattern
    matches = re.findall(pattern, text)

    if matches:
        # Joining the matches into a single string and converting it to an integer
        return int("".join(matches))
    else:
        return 0


def get_neighborhood_data(postcode: str):
    pc4 = postcode[:4]
    condition = neighborhood_csv_data["pc4"] == int(pc4)
    df = neighborhood_csv_data[condition]
    if len(df) > 0:
        return df.iloc[0]
    else:
        return None
