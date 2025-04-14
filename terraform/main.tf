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
        image = "gcr.io/${var.project_id}/${var.repository}:${var.image_tag}"
        
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
