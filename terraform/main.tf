terraform {
  required_version = ">= 1.4.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
}

provider "google" {
  project = "aiops-bone-zone"
  region  = "europe-west2"
}

# New variable to accept environment suffix
variable "env_suffix" {
  type    = string
  default = "dev"
}

resource "google_service_account" "service" {
  account_id   = "cloud-run-exec-${var.env_suffix}"
  display_name = "Cloud Run Execution SA"
}

resource "google_cloud_run_service" "tiny_llm_service" {
  name     = "tiny-llm-service-${var.env_suffix}"
  location = "europe-west2"

  template {
    spec {
      service_account_name = google_service_account.service.email
      containers {
        image = "europe-west2-docker.pkg.dev/aiops-bone-zone/tiny-llm-app/tiny-llm-app:latest"
        ports {
          name           = "http1"
          container_port = 8000
        }
      }
    }
  }
  autogenerate_revision_name = true
}

resource "google_cloud_run_service_iam_member" "noauth" {
  location = google_cloud_run_service.tiny_llm_service.location
  project  = google_cloud_run_service.tiny_llm_service.project
  service  = google_cloud_run_service.tiny_llm_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "cloud_run_url" {
  description = "URL of ephemeral Cloud Run service"
  value       = google_cloud_run_service.tiny_llm_service.status[0].url
}
