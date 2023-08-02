from bs4 import BeautifulSoup
import requests
from datetime import datetime
import re
import os
from constants import HEADERS
import os
from common.utils import get_int_from_string, get_neighborhood_data

directory = os.path.dirname(os.path.realpath(__file__))

env = os.getenv("ENV")


def get_svg_type(path: str):
    if "M38.5 32.25v-16.5a5" in path:
        return "floor-space"
    if "M11 20l-3.999" in path:
        return "bedrooms"
    if "M23.675 12.891l-6.852" in path:
        return "energy label"

    return "unknown"


def get_postal_code(text: str):
    pattern = r"(\d{4})(.+)?([A-Z]{2})"

    matches = re.findall(pattern, text)

    if matches[0] and len(matches[0]) == 3:
        return matches[0][0] + matches[0][2]
    else:
        return "Invalid postcode: " + text


def scrape_funda(env: str, base_url: str, search_url: str):
    if base_url is None:
        print("FUNDA_BASE_URL is not set")
        return

    houses = []

    for x in range(1, 4):
        if env == "dev":
            print("[DEV] Scraping: ", base_url)
            soup = BeautifulSoup(
                open(f"{directory}test-html/funda-test.html"), "html.parser"
            )
        else:
            url = base_url + search_url + f"&search_result={x}"
            response = requests.get(url, headers=HEADERS)
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
