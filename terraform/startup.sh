#!/bin/bash
# VM boot: install system deps only. Code + .env arrive via SCP.
set -e
apt-get update
apt-get install -y python3-venv python3-pip
mkdir -p /opt/ashjob-bot
echo "VM ready for code upload" > /opt/ashjob-bot/READY
