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

variable "repository" {
  description = "The Artifact Registry repository name"
  type        = string
  default     = "tiny-llm-app"
}

variable "image_tag" {
  description = "The Docker image tag to deploy (defaults to latest if not provided)"
  type        = string
  default     = "latest"
}

variable "service_name" {
  description = "The name of the Cloud Run service"
  type        = string
  default     = "tiny-llm-service"
}

variable "container_port" {
  description = "The port the container listens on"
  type        = number
  default     = 8000
}

variable "min_instances" {
  description = "Minimum number of instances to keep running"
  type        = string
  default     = "0"
}

variable "max_instances" {
  description = "Maximum number of instances to scale to"
  type        = string
  default     = "4"
}

variable "cpu" {
  description = "CPU allocation for each instance"
  type        = string
  default     = "1"
}

variable "memory" {
  description = "Memory allocation for each instance"
  type        = string
  default     = "2Gi"
}

variable "timeout_seconds" {
  description = "Maximum time a request can take before timing out"
  type        = number
  default     = 300
}

variable "service_account_name" {
  description = "The name of the service account for Cloud Run"
  type        = string
  default     = "cloud-run-exec"
}

variable "allow_unauthenticated" {
  description = "Whether to allow unauthenticated access to the service"
  type        = bool
  default     = true
}
