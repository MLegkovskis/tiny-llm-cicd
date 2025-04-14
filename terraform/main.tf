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
  project = var.project_id
  region  = var.region
}

# The rest of the variables are defined in variables.tf

# Check if the service account already exists
data "google_service_account" "existing" {
  account_id = var.service_account_name
  project    = var.project_id
  # This will fail if the service account doesn't exist, which is fine
  # Terraform will handle this gracefully
}

# Local variable to determine if we need to create a new service account
locals {
  service_account_exists = can(data.google_service_account.existing.email)
  service_account_email = local.service_account_exists ? data.google_service_account.existing.email : google_service_account.service[0].email
}

# Create service account only if it doesn't exist
resource "google_service_account" "service" {
  count        = local.service_account_exists ? 0 : 1
  account_id   = var.service_account_name
  display_name = "Cloud Run Execution SA"
}

resource "google_cloud_run_service" "tiny_llm_service" {
  name     = var.service_name
  location = var.region

  template {
    spec {
      service_account_name = local.service_account_email
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repository}/${var.repository}:${var.image_tag}"
        
        ports {
          name           = "http1"
          container_port = var.container_port
        }
        
        resources {
          limits = {
            cpu    = var.cpu
            memory = var.memory
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
      
      # Set container concurrency and timeout
      container_concurrency = 80
      timeout_seconds       = var.timeout_seconds
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = var.min_instances
        "autoscaling.knative.dev/maxScale" = var.max_instances
      }
    }
  }
  
  autogenerate_revision_name = true
  
  # Define traffic routing
  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Allow unauthenticated access if specified
resource "google_cloud_run_service_iam_member" "noauth" {
  count    = var.allow_unauthenticated ? 1 : 0
  location = var.region
  project  = var.project_id
  service  = google_cloud_run_service.tiny_llm_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "cloud_run_url" {
  value = google_cloud_run_service.tiny_llm_service.status[0].url
}

output "service_name" {
  value = google_cloud_run_service.tiny_llm_service.name
}

output "region" {
  value = var.region
}

output "project_id" {
  value = var.project_id
}
