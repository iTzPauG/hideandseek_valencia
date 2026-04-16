variable "project_id" {
  default = "hidenseekpau"
}

variable "region" {
  default = "europe-west1"
}

variable "db_password" {
  description = "Cloud SQL app user password"
  sensitive   = true
}

variable "jwt_secret" {
  description = "JWT signing secret"
  sensitive   = true
}
