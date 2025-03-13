# Amsterdam House Price Scraper

This repo contains two applications which can be deployed to GCP Cloud Run.

The first is a scraper to collect data on the price of new houses listed in Amsterdam.

The second is an emailer which sends an email with the latest listings.

## Scraper

This application scrapes the house price data from the website of the city of Amsterdam. The data is collected from [Funda](https://www.funda.nl/) and [Pararius](https://www.pararius.nl/).

## Emailer

Sends an email with the latest data added to BigQuery from the scraper, for easy browsing using Gmail.

## Deployment

The easiest way to deploy the applications is to build both of the docker images using the provided Dockerfiles and push them to a container registry.

The images can then be used as a Cloud Run Job, with a cron trigger.
