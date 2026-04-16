terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ── Artifact Registry ──────────────────────────────────────────────────────────
resource "google_artifact_registry_repository" "repo" {
  repository_id = "hidenseek"
  format        = "DOCKER"
  location      = var.region
}

locals {
  registry = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.repository_id}"
}

# ── Docker builds ──────────────────────────────────────────────────────────────
resource "null_resource" "build_backend" {
  triggers = { always = timestamp() }
  provisioner "local-exec" {
    command = <<-EOT
      gcloud auth configure-docker ${var.region}-docker.pkg.dev --quiet
      docker build --platform linux/amd64 -t ${local.registry}/backend:latest ../backend
      docker push ${local.registry}/backend:latest
    EOT
  }
  depends_on = [google_artifact_registry_repository.repo]
}

resource "null_resource" "build_frontend" {
  triggers = { always = timestamp() }
  provisioner "local-exec" {
    command = <<-EOT
      docker build \
        --platform linux/amd64 \
        --build-arg VITE_API_URL=/api \
        -t ${local.registry}/frontend:latest ../frontend
      docker push ${local.registry}/frontend:latest
    EOT
  }
  depends_on = [google_artifact_registry_repository.repo]
}

# ── Cloud SQL ──────────────────────────────────────────────────────────────────
resource "google_sql_database_instance" "pg" {
  name             = "hidenseek-pg"
  database_version = "POSTGRES_15"
  region           = var.region
  deletion_protection = false

  settings {
    tier = "db-f1-micro"
    ip_configuration {
      ipv4_enabled = true
    }
  }
}

resource "google_sql_database" "db" {
  name     = "hidenseek"
  instance = google_sql_database_instance.pg.name
}

resource "google_sql_user" "app" {
  name     = "appuser"
  instance = google_sql_database_instance.pg.name
  password = var.db_password
}

# ── Secret Manager ─────────────────────────────────────────────────────────────
resource "google_secret_manager_secret" "db_password" {
  secret_id = "db-password"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = var.db_password
}

resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "jwt-secret"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "jwt_secret" {
  secret      = google_secret_manager_secret.jwt_secret.id
  secret_data = var.jwt_secret
}

# ── Service Account ────────────────────────────────────────────────────────────
resource "google_service_account" "backend_sa" {
  account_id   = "hidenseek-backend"
  display_name = "Hide & Seek Backend SA"
}

resource "google_project_iam_member" "firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_project_iam_member" "cloudsql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "db_secret_access" {
  secret_id = google_secret_manager_secret.db_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "jwt_secret_access" {
  secret_id = google_secret_manager_secret.jwt_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_sa.email}"
}

# ── Cloud Run: Backend ─────────────────────────────────────────────────────────
resource "google_cloud_run_v2_service" "backend" {
  name     = "hidenseek-backend"
  location = var.region

  template {
    service_account = google_service_account.backend_sa.email

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.pg.connection_name]
      }
    }

    containers {
      image = "${local.registry}/backend:latest"

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name = "DATABASE_URL"
        value = "postgresql+asyncpg://appuser:${var.db_password}@/hidenseek?host=/cloudsql/${google_sql_database_instance.pg.connection_name}"
      }
      env {
        name = "SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.jwt_secret.secret_id
            version = "latest"
          }
        }
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      resources {
        limits = { cpu = "1", memory = "512Mi" }
      }
    }
  }

  depends_on = [null_resource.build_backend]
}

resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ── Cloud Run: Frontend ────────────────────────────────────────────────────────
resource "google_cloud_run_v2_service" "frontend" {
  name     = "hidenseek-frontend"
  location = var.region

  template {
    containers {
      image = "${local.registry}/frontend:latest"

      env {
        name  = "BACKEND_URL"
        value = google_cloud_run_v2_service.backend.uri
      }

      resources {
        limits = { cpu = "1", memory = "512Mi" }
      }
    }
  }

  depends_on = [null_resource.build_frontend, google_cloud_run_v2_service.backend]
}

resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ── Firestore ──────────────────────────────────────────────────────────────────
resource "google_firestore_database" "default" {
  name        = "(default)"
  location_id = "eur3"
  type        = "FIRESTORE_NATIVE"
}

# ── Seed Firestore after deploy ────────────────────────────────────────────────
resource "null_resource" "seed_firestore" {
  triggers = { always = timestamp() }
  provisioner "local-exec" {
    command = "cd ../scripts && pip install google-cloud-firestore -q && python seed_firestore.py"
    environment = {
      GOOGLE_CLOUD_PROJECT = var.project_id
    }
  }
  depends_on = [google_firestore_database.default]
}
