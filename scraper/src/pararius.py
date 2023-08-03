from constants import HEADERS
from bs4 import BeautifulSoup
import os
import requests
from datetime import datetime
import re
from common.utils import get_int_from_string, get_neighborhood_data

directory = os.path.dirname(os.path.realpath(__file__))


def get_postal_code(text: str):
    pattern = r"(\d{4})(.+)?([A-Z]{2})"

    matches = re.findall(pattern, text)

    if matches[0] and len(matches[0]) == 3:
        return matches[0][0] + matches[0][2]
    else:
        return "Invalid postcode: " + text


def get_postal_code_city(text: str):
    pattern = r"(.+) \("

    matches = re.findall(pattern, text)

    if matches[0]:
        return matches[0]
    else:
        return "Invalid postcode - city: " + text


def scrape_pararius(env: str, base_url: str, search_url: str):
    if base_url is None:
        print("PARARIUS_BASE_URL is not set")
        return

    houses = []

    for x in range(1, 4):
        if env == "dev":
            if x > 1:
                return

            print("[DEV] Scraping: ", base_url)
            house_html = BeautifulSoup(
                open(f"{directory}/test-html/pararius-test.html"), "html.parser"
            )
        else:
            base_url = base_url + f"/page-{x}"  # TODO: UPDATE THIS
            response = requests.get(base_url, headers=HEADERS)
            print("Scraping: ", base_url)
            house_html = BeautifulSoup(response.content, "html.parser")

        all_houses = house_html.find_all("section", class_="listing-search-item")

        for list_item in all_houses:
            house_name_number = list_item.find(
                "h2", class_="listing-search-item__title"
            ).text.strip()
            house_sub_title = list_item.find(
                "div", class_="listing-search-item__sub-title'"
            ).text.strip()

            postal_code = get_postal_code(house_sub_title)
            postal_code_city = get_postal_code_city(house_sub_title)

            price_sale = get_int_from_string(
                list_item.find("div", class_="listing-search-item__price").text.strip()
            )

            floor_space = get_int_from_string(
                list_item.find(
                    "li", class_="illustrated-features__item--surface-area"
                ).text.strip()
            )

            link = (
                base_url
                + list_item.find("a", class_="listing-search-item__link")["href"]
            )

            listing = requests.get(link, headers=HEADERS)
            listing_html = BeautifulSoup(listing.content, "html.parser")

            try:
                bedrooms = listing_html.find(
                    "dd", class_="listing-features__description--number_of_bedrooms"
                ).text.strip()
            except:
                bedrooms = 0

            neighborhood_data = get_neighborhood_data(postal_code)

            img = list_item.find("wc-picture", class_="picture--list").find("img")[
                "src"
            ]

            property_data = {
                "id": house_name_number + " " + postal_code_city,
                "house_name_number": house_name_number,
                "price_sale": price_sale,
                "postal_code": postal_code,
                "floor_space": floor_space,
                "bedrooms": bedrooms,
                # "energy_label": energy_label,
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
