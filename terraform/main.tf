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
  project = "tiny-llm-cicd"
  region  = "europe-west2"
}

# Add this variable to support the CI/CD workflow
variable "image_tag" {
  description = "The Docker image tag to deploy"
  type        = string
  default     = "latest"
}

resource "google_service_account" "service" {
  account_id   = "cloud-run-exec"
  display_name = "Cloud Run Execution SA"
}

resource "google_cloud_run_service" "tiny_llm_service" {
  name     = "tiny-llm-service"
  location = "europe-west2"

  template {
    spec {
      service_account_name = google_service_account.service.email
      containers {
        image = "europe-west2-docker.pkg.dev/tiny-llm-cicd/tiny-llm-app/tiny-llm-app:${var.image_tag}"
        
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
      
      # Set container concurrency and timeout
      container_concurrency = 80
      timeout_seconds       = 300
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

# Allow unauthenticated
resource "google_cloud_run_service_iam_member" "noauth" {
  location = "europe-west2"
  project  = "tiny-llm-cicd"
  service  = google_cloud_run_service.tiny_llm_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "cloud_run_url" {
  value = google_cloud_run_service.tiny_llm_service.status[0].url
}
