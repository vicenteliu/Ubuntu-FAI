#!/bin/bash
# FAI environment configuration
# Dynamically generated from user configuration
# Generated at: 2025-07-18T13:43:24.747370

# Export configuration variables for use in FAI scripts
export FAI_USER_NAME="testuser"
export FAI_USER_FULL_NAME="Test User"
export FAI_SUDO_NOPASSWD="false"
export FAI_HARDWARE_VENDOR="dell"
export FAI_TARGET_SSD="true"
export FAI_ENCRYPTION_ENABLED="true"
export FAI_HOSTNAME="ubuntu-fai-test"
export FAI_DHCP="true"
export FAI_FIRST_BOOT_ENABLED="true"
export FAI_BUILD_TIMESTAMP="2025-07-18T13:43:24.747358"
export FAI_ISO_LABEL="Ubuntu-FAI"
export LUKS_CIPHER="aes-xts-plain64"
export LUKS_KEY_SIZE="256"
export LUKS_HASH="sha256"
export CUSTOM_APT_PACKAGES="git curl vim"
export CUSTOM_SNAP_PACKAGES="code"

# Log environment setup
echo "$(date): FAI environment configured" >> $LOGDIR/environment.log
