terraform {
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.0" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

resource "google_service_account" "bot" {
  account_id   = "ashjob-bot-vm"
  display_name = "AshJob Bot VM"
}

resource "google_compute_instance" "bot" {
  name         = "ashjob-bot"
  machine_type = "e2-micro"
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = 30
      type  = "pd-standard"
    }
  }

  network_interface {
    network = "default"
    access_config {}
  }

  service_account {
    email  = google_service_account.bot.email
    scopes = ["cloud-platform"]
  }

  metadata_startup_script = file("${path.module}/startup.sh")
  tags = ["ashjob-bot"]
}

resource "google_compute_firewall" "ssh" {
  name    = "ashjob-bot-allow-ssh"
  network = "default"
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["ashjob-bot"]
}

output "vm_ip" {
  value = google_compute_instance.bot.network_interface[0].access_config[0].nat_ip
}
