#!/bin/bash
# FAI environment configuration
# Dynamically generated from user configuration
# Generated at: 2025-07-18T14:11:48.147950

# Export configuration variables for use in FAI scripts
export FAI_USER_NAME="ubuntu"
export FAI_USER_FULL_NAME="System Administrator"
export FAI_SUDO_NOPASSWD="false"
export FAI_HARDWARE_VENDOR="dell"
export FAI_TARGET_SSD="true"
export FAI_ENCRYPTION_ENABLED="true"
export FAI_HOSTNAME="ubuntu-fai-desktop"
export FAI_DHCP="true"
export FAI_FIRST_BOOT_ENABLED="true"
export FAI_BUILD_TIMESTAMP="2025-07-18T14:11:48.147942"
export FAI_ISO_LABEL="Ubuntu-24.04-FAI"
export LUKS_CIPHER="aes-xts-plain64"
export LUKS_KEY_SIZE="256"
export LUKS_HASH="sha256"
export CUSTOM_APT_PACKAGES="curl wget git vim htop build-essential python3-pip docker.io firefox libreoffice gimp vlc thunderbird"
export CUSTOM_DEB_URLS="https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb,https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64"
export CUSTOM_SNAP_PACKAGES="discord,slack,zoom-client"
export FAI_SSH_KEYS="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKqP7j8Qv0hBJ7rMN3bNGkGl9L8FhZ7x admin@workstation\nssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDExample... admin@laptop"

# Log environment setup
echo "$(date): FAI environment configured" >> $LOGDIR/environment.log
