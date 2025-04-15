terraform {
  required_version = ">= 1.4.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
}

# Define all variables directly in this file
variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "tiny-llm-cicd"
}

variable "region" {
  description = "The GCP region to deploy resources to"
  type        = string
  default     = "europe-west2"
}

variable "service_account_name" {
  description = "The name of the service account for Cloud Run"
  type        = string
  default     = "cloud-run-exec"
}

variable "service_name" {
  description = "The name of the Cloud Run service"
  type        = string
  default     = "tiny-llm-service"
}

variable "image_tag" {
  description = "The Docker image tag to deploy"
  type        = string
  default     = "latest"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_service_account" "service" {
  account_id   = var.service_account_name
  display_name = "Cloud Run Execution SA"
}

resource "google_cloud_run_service" "tiny_llm_service" {
  name     = var.service_name
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.service.email
      containers {
        # Use the image_tag variable
        image = "gcr.io/tiny-llm-cicd/tiny-llm-app:${var.image_tag}"
        
        ports {
          name           = "http1"
          container_port = 8000
        }
        
        resources {
          limits = {
            cpu    = "1"
            memory = "2Gi"
          }
        }
        
        # Add health checks
        liveness_probe {
          http_get {
            path = "/health"
          }
          initial_delay_seconds = 10
          timeout_seconds       = 5
          period_seconds        = 15
          failure_threshold     = 3
        }
        
        startup_probe {
          http_get {
            path = "/health"
          }
          initial_delay_seconds = 5
          timeout_seconds       = 5
          period_seconds        = 5
          failure_threshold     = 12  # Allow 60 seconds for startup (12 * 5s)
        }
      }
      
      timeout_seconds = 300
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "0"
        "autoscaling.knative.dev/maxScale" = "4"
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  autogenerate_revision_name = true
}

# IAM policy to allow unauthenticated access to the service
resource "google_cloud_run_service_iam_member" "public" {
  service  = google_cloud_run_service.tiny_llm_service.name
  location = google_cloud_run_service.tiny_llm_service.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Output the service URL
output "service_url" {
  value = google_cloud_run_service.tiny_llm_service.status[0].url
}
