from bs4 import BeautifulSoup
import requests
from google.cloud import bigquery
import re
import os
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd

load_dotenv()

gcp_project = os.getenv("GCP_PROJECT")
service_account_path = os.getenv("SERVICE_ACCOUNT_PATH")
bq_dataset = os.getenv("BQ_DATASET")
bq_table = os.getenv("BQ_TABLE")
env = os.getenv("ENV")

print("ENV: ", gcp_project, service_account_path, bq_dataset, bq_table)

# Set up BigQuery client

client = (
    bigquery.Client.from_service_account_json(service_account_path)
    if env == "dev"
    else bigquery.Client()
)

neighborhood_csv_data = pd.read_csv(f"./pc4.csv")


def get_svg_type(path: str):
    if "M38.5 32.25v-16.5a5" in path:
        return "floor-space"
    if "M11 20l-3.999" in path:
        return "bedrooms"
    if "M23.675 12.891l-6.852" in path:
        return "energy label"

    return "unknown"


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


def get_postal_code(text: str):
    pattern = r"(\d{4})(.+)?([A-Z]{2})"

    matches = re.findall(pattern, text)

    if matches[0] and len(matches[0]) == 3:
        return matches[0][0] + matches[0][2]
    else:
        return "Invalid postcode " + text


def get_neighborhood_data(postcode: str):
    pc4 = postcode[:4]
    condition = neighborhood_csv_data["pc4"] == int(pc4)
    df = neighborhood_csv_data[condition]
    if len(df) > 0:
        return df.iloc[0]
    else:
        return None


def scrape_funda():
    base_url = os.getenv("FUNDA_BASE_URL")

    if base_url is None:
        print("FUNDA_BASE_URL is not set")
        return

    houses = []

    # Send a GET request to the URL and retrieve the HTML content
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for x in range(1, 4):
        if env == "dev":
            print("[DEV] Scraping: ", base_url)
            soup = BeautifulSoup(open("../test-page.html"), "html.parser")
        else:
            url = base_url + f"&search_result={x}"
            response = requests.get(url, headers=headers)
            print("Scraping: ", url)
            soup = BeautifulSoup(response.content, "html.parser")

        # Extract the desired properties from the HTML
        all_houses = soup.find_all("div", {"data-test-id": "search-result-item"})

        for search_result_item in all_houses:
            house_name_number = search_result_item.find(
                "h2", {"data-test-id": "street-name-house-number"}
            ).text.strip()
            price_sale_element = search_result_item.find(
                "p", {"data-test-id": "price-sale"}
            )
            price_sale = get_int_from_string(price_sale_element.text.strip())
            postal_code_city = search_result_item.find(
                "div", {"data-test-id": "postal-code-city"}
            ).text.strip()
            link = search_result_item.find("a", {"data-test-id": "object-image-link"})[
                "href"
            ]

            imgSources = search_result_item.find(
                "img", {"alt": lambda x: x and "main image" in x}
            )["srcset"].split(" ")
            img = imgSources[1][5:] if len(imgSources) > 1 else ""

            floor_space = 0
            bedrooms = 0
            energy_label = ""

            attributes_list = price_sale_element.find_next("ul")
            attributes = attributes_list.find_all("li")
            for attribute in attributes:
                svg_path = attribute.find_next("path")["d"]
                svg_type = get_svg_type(svg_path)
                li_text = attribute.text.strip()

                match svg_type:
                    case "floor-space":
                        floor_space = get_int_from_string(li_text)

                    case "bedrooms":
                        bedrooms = get_int_from_string(li_text)

                    case "energy label":
                        energy_label = li_text.strip()

            postcode = get_postal_code(postal_code_city)
            neighborhood_data = get_neighborhood_data(postcode)

            # # Create a dictionary representing the property data
            property_data = {
                "id": house_name_number + " " + postal_code_city,
                "house_name_number": house_name_number,
                "price_sale": price_sale,
                "postal_code": postcode,
                "floor_space": floor_space,
                "bedrooms": bedrooms,
                "energy_label": energy_label,
                "price_per_m2": int(price_sale / floor_space) if floor_space > 0 else 0,
                "link": link,
                "inserted_date": datetime.now().isoformat(),
                "neighborhood": neighborhood_data["Naam buurt"]
                if neighborhood_data is not None
                else "",
                "wijk": neighborhood_data["Naam Wijk"]
                if neighborhood_data is not None
                else "",
                "zone": neighborhood_data["Naam stadsdeel"]
                if neighborhood_data is not None
                else "",
                "image": img,
            }

            houses.append(property_data)

    return houses


def write_to_bigquery(rows):
    # Big query table Id
    table_id = f"{gcp_project}.{bq_dataset}.{bq_table}"

    for row in rows:
        # Check if row already exists in BigQuery
        query = f'SELECT * FROM `{table_id}` where id="{row["id"]}" LIMIT 1'
        results = client.query(query).result()
        results_list = list(results)

        if len(results_list) == 0:
            # Insert the rows into BigQuery table
            errors = client.insert_rows_json(
                table_id,
                [row],
            )

            if errors:
                print(f"Encountered errors while inserting {row.id}: {errors}")
            else:
                print(f"Successfully inserted {row['id']}")
        else:
            print(f"Row with id {row['id']} already exists in BigQuery.")


# Scrape the properties
funda_houses = scrape_funda()

# Write the funda_houses to BigQuery
# write_to_bigquery(funda_houses)
