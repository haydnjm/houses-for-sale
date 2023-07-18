provider "google" {
  credentials = file("../service-account.json")
  project     = "houses-for-sale"
  region      = "europe-west4"
}

resource "google_project" "houses_for_sale_google_project" {
  name       = "houses-for-sale"
  project_id = "houses-for-sale-392908"
}

resource "google_cloud_run_service" "cloud_run" {
  name     = "get-houses"
  location = "europe-west4"
  project = "houses-for-sale-392908"

  template {
    spec {
      containers {
        image = "europe-west4-docker.pkg.dev/houses-for-sale-392908/houses-for-sale/houses-for-sale:latest"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}