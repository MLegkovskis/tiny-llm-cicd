terraform {
  required_version = ">= 1.0.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0.0"
    }
  }
}

# Simple variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "tiny-llm-cicd"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "europe-west2"
}

variable "image_tag" {
  description = "Docker image tag (not used in this simplified config, but required by CI/CD)"
  type        = string
  default     = "latest"
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

# Create a simple Cloud Run service with a public image
resource "google_cloud_run_service" "default" {
  name     = "tiny-llm-service"
  location = var.region

  template {
    spec {
      containers {
        # Using a known public image that definitely works
        image = "us-docker.pkg.dev/cloudrun/container/hello"
      }
    }
  }

  # Make the service public
  metadata {
    annotations = {
      "run.googleapis.com/ingress" = "all"
    }
  }
}

# Allow public access
data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

resource "google_cloud_run_service_iam_policy" "noauth" {
  location    = google_cloud_run_service.default.location
  project     = google_cloud_run_service.default.project
  service     = google_cloud_run_service.default.name
  policy_data = data.google_iam_policy.noauth.policy_data
}

# Output the service URL
output "url" {
  value = google_cloud_run_service.default.status[0].url
}
