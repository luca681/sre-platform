# ============================================================
# Terraform Configuration — Local Docker Infrastructure
# ============================================================
# This file describes the infrastructure we want to exist.
# Terraform reads this and makes reality match the description.

# ── Terraform settings block ─────────────────────────────────
# This tells Terraform which version it needs and which
# providers (plugins) to download.

terraform {
  required_version = ">= 1.0"          # minimum Terraform version

  required_providers {
    docker = {
      # The Docker provider lets Terraform manage Docker
      # containers, images and networks on your local machine.
      # "kreuzwerker/docker" is the provider's registry path.
      source  = "kreuzwerker/docker"
      version = "~> 3.0"               # use any 3.x version
    }
  }
}

# ── Provider configuration ────────────────────────────────────
# Tells the Docker provider where Docker is running.
# On Linux, Docker listens on a Unix socket at this path.
# This is the same socket Docker CLI uses when you run
# "docker ps" or "docker compose up".

provider "docker" {
  host = "unix:///var/run/docker.sock"
}

# ── Data source: pull the Nginx image ─────────────────────────
# A "data source" reads existing information rather than
# creating something new. Here we're telling Terraform:
# "find or pull the nginx:alpine image from Docker Hub."
#
# "alpine" is a minimal Linux distribution — the image is
# only 40MB vs 180MB for the full Nginx image.

resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  # keep_locally = true means don't delete the image when
  # you run "terraform destroy". The container will be
  # removed but the downloaded image stays on disk.
  keep_locally = true
}

# ── Resource: create an Nginx container ───────────────────────
# This is the main resource — a running Docker container.
# "docker_container" is the resource TYPE (from the provider).
# "web_server" is our NAME for this resource — used to
# reference it elsewhere in the config.
#
# Think of it like a variable name for this piece of infra.

resource "docker_container" "web_server" {
  # Which image to use — references the image resource above.
  # The dot notation reads: docker_image.nginx.image_id
  # resource_type . resource_name . attribute
  image = docker_image.nginx.image_id

  # The container's name inside Docker
  name  = "sre-nginx-terraform"

  # must_run = true tells Terraform to ensure the container
  # is always running. If it stops, Terraform will restart it
  # on the next apply.
  must_run = true

  # Port mapping: forward host port 8080 to container port 80.
  # This means http://localhost:8080 reaches Nginx inside
  # the container. We use 8080 instead of 80 because Apache
  # is already using port 80 on your machine.
  ports {
    internal = 80      # port inside the container
    external = 8080    # port on your host machine
  }
}

# ── Output values ──────────────────────────────────────────────
# Outputs print useful information after Terraform runs.
# Like function return values — they surface data you care about.
# You can also use outputs to pass values between modules.

output "container_name" {
  description = "The name of the created container"
  value       = docker_container.web_server.name
}

output "access_url" {
  description = "URL to access the web server"
  value       = "http://localhost:8080"
}
