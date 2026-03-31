#!/bin/bash
set -e

# Python dependencies
uv sync

# Claude Code (optional)
read -p "Install Claude Code? [y/N] " install_claude
if [[ "$install_claude" =~ ^[Yy]$ ]]; then
    if [ -f /root/.claude/.claude.json ] && [ ! -f /root/.claude.json ]; then
        ln -s /root/.claude/.claude.json /root/.claude.json
    fi
    curl -fsSL https://claude.ai/install.sh | bash
fi

# Pulumi (optional - for managing GCP infrastructure)
read -p "Install Pulumi? [y/N] " install_pulumi
if [[ "$install_pulumi" =~ ^[Yy]$ ]]; then
    curl -fsSL https://get.pulumi.com | sh
fi

# Google Cloud CLI (optional - for GCP deployment)
read -p "Install Google Cloud CLI? [y/N] " install_gcloud
if [[ "$install_gcloud" =~ ^[Yy]$ ]]; then
    ARCH=$(uname -m)
    case "$ARCH" in
        x86_64)  GCLOUD_ARCH="x86_64" ;;
        aarch64) GCLOUD_ARCH="arm" ;;
        *)       echo "Unsupported architecture: $ARCH" && exit 1 ;;
    esac
    cd /opt
    curl -O "https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-${GCLOUD_ARCH}.tar.gz"
    tar -xf "google-cloud-cli-linux-${GCLOUD_ARCH}.tar.gz"
    rm "google-cloud-cli-linux-${GCLOUD_ARCH}.tar.gz"
    ./google-cloud-sdk/install.sh --quiet --path-update false
    gcloud init
fi
