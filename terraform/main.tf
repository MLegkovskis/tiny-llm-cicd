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

# Get the image tag from environment variables
variable "image_tag" {
  description = "The Docker image tag to deploy (defaults to latest if not provided)"
  type        = string
  default     = "latest"
}

variable "project_id" {
  description = "The ID of the project"
  type        = string
}

variable "region" {
  description = "The region of the project"
  type        = string
}

variable "service_account_name" {
  description = "The name of the service account"
  type        = string
}

variable "service_name" {
  description = "The name of the service"
  type        = string
}

variable "repository" {
  description = "The name of the repository"
  type        = string
}

variable "container_port" {
  description = "The port of the container"
  type        = number
}

variable "cpu" {
  description = "The CPU limit of the container"
  type        = string
}

variable "memory" {
  description = "The memory limit of the container"
  type        = string
}

variable "timeout_seconds" {
  description = "The timeout of the container"
  type        = number
}

variable "min_instances" {
  description = "The minimum number of instances"
  type        = string
}

variable "max_instances" {
  description = "The maximum number of instances"
  type        = string
}

variable "allow_unauthenticated" {
  description = "Whether to allow unauthenticated access"
  type        = bool
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
