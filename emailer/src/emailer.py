from datetime import datetime, timedelta
import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.cloud import bigquery
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()

env = os.getenv("ENV")
sender_email = os.getenv("SENDER") or ""
email_password = os.getenv("EMAIL_PASSWORD") or ""
gcp_project = os.getenv("GCP_PROJECT")
service_account_path = os.getenv("SERVICE_ACCOUNT_PATH")
bq_dataset = os.getenv("BQ_DATASET")
filters_table = os.getenv("FILTERS_TABLE")
houses_table = os.getenv("HOUSES_TABLE")

smtp_server = "smtp.gmail.com"  # Replace with your SMTP server address
smtp_port = 587  # Replace with the appropriate port for your SMTP server

bq_client = (
    bigquery.Client.from_service_account_json(service_account_path)
    if env == "dev"
    else bigquery.Client()
)
email_service = build("gmail", "v1")


def build_house_query(filter: dict):
    base_table_id = f"{gcp_project}.{bq_dataset}"

    current_time = datetime.now()
    current_time_minus_one_hour = current_time - timedelta(minutes=30)
    query = f"""
        SELECT * FROM `{base_table_id}.{houses_table}`
        WHERE inserted_date >= '{current_time_minus_one_hour.isoformat()}'
    """

    if filter["min_price"] is not None:
        query += f" AND price_sale >= {filter['min_price']}"
    if filter["max_price"] is not None:
        query += f" AND price_sale <= {filter['max_price']}"
    if filter["min_price_per_m2"] is not None:
        query += f" AND price_per_m2 >= {filter['min_price_per_m2']}"
    if filter["max_price_per_m2"] is not None:
        query += f" AND price_per_m2 <= {filter['max_price_per_m2']}"
    if filter["min_bedrooms"] is not None:
        query += f" AND bedrooms >= {filter['min_bedrooms']}"
    if filter["max_bedrooms"] is not None:
        query += f" AND bedrooms <= {filter['max_bedrooms']}"
    if filter["min_floor_space"] is not None:
        query += f" AND floor_space >= {filter['min_floor_space']}"
    if filter["max_floor_space"] is not None:
        query += f" AND floor_space <= {filter['max_floor_space']}"

    return query


# Create a message for an email via the gmail api
def create_message(recipient, subject, content):
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient
    message["Subject"] = subject
    message.attach(MIMEText(content, "html"))
    return message


def send_email_for_house(recipient_email: str, house: dict):
    formatted_price = int(house["price_sale"] / 1000)
    subject = f"{house['id']}"
    content = f"""
        {f'<img src="{house["image"]}" />' if house["image"] else ""}
        <p>{house['neighborhood']}, {house['wijk']}, {house['zone']}</p>
        <p>€{formatted_price}k</p>
        <p>{house['floor_space']}m2</p>
        <p>{int(house['price_per_m2'])}€/m2</p>
        <p>{house['bedrooms']} bedrooms</p>
        <h3><a href='{house['link']}'>To listing</a></h3>
        <h3><a href='{house['link']}#kaart'>To map</a></h3>
    """

    message = create_message(recipient_email, subject, content)

    server = smtplib.SMTP(smtp_server, smtp_port)
    try:
        # Connect to the SMTP server
        server.starttls()  # Upgrade the connection to a secure encrypted one

        # Log in to the SMTP server
        # Replace 'your_email_password' with your email account password or app-specific password
        server.login(sender_email, email_password)

        # Send the email
        server.sendmail(sender_email, recipient_email, message.as_string())

        print(f"Email sent successfully to {recipient_email} for house {house['id']}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the SMTP connection
        server.quit()


# Get all houses that need to be emailed since the last trigger
def main():
    # First, get all filters
    base_table_id = f"{gcp_project}.{bq_dataset}"
    filters_query = f"SELECT * FROM `{base_table_id}.{filters_table}` LIMIT 1"
    filters = list(bq_client.query(filters_query).result())

    if len(filters) == 0:
        print("No filters found with query ", filters_query)
        return []

    # TODO: Send emails to different user per filter
    # Get all houses that belongs to each filter
    for filter in filters:
        if filter["email"] is None:
            print("No email found for filter ", filter)
            continue

        houses_query = build_house_query(filter)

        houses_result = bq_client.query(houses_query).result()
        houses = list(houses_result)

        print(f"{len(houses)} houses found!")

        for house in houses:
            send_email_for_house(filter["email"], house)


main()
