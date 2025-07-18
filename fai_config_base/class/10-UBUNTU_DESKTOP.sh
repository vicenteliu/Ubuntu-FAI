#!/bin/bash
# FAI class script for Ubuntu Desktop base configuration
# This script defines the base Ubuntu Desktop installation class

# Set error handling
set -euo pipefail

# Define base Ubuntu Desktop class
echo "UBUNTU_DESKTOP"

# Set FAI variables for Ubuntu Desktop installation
export FAI_DISTRIBUTION="ubuntu"
export FAI_RELEASE="noble"  # Ubuntu 24.04 LTS codename
export FAI_ARCH="amd64"

# Desktop environment selection
export DESKTOP_ENVIRONMENT="gnome"

# Package management
export APT_PROXY=""  # Can be set if using local APT proxy
export DEBIAN_FRONTEND="noninteractive"

# Installation mirrors
export UBUNTU_MIRROR="http://archive.ubuntu.com/ubuntu"
export UBUNTU_SECURITY_MIRROR="http://security.ubuntu.com/ubuntu"

# Locale and timezone settings (defaults)
export DEFAULT_LOCALE="en_US.UTF-8"
export DEFAULT_TIMEZONE="UTC"
export DEFAULT_KEYBOARD="us"

# User account defaults
export DEFAULT_SHELL="/bin/bash"

# System settings
export GRUB_TIMEOUT="5"
export SWAP_SIZE="2048"  # MB

# Package categories to install
export INSTALL_DESKTOP="yes"
export INSTALL_MULTIMEDIA="yes"
export INSTALL_OFFICE="yes"
export INSTALL_DEVELOPMENT="no"  # Controlled by configuration

# Network configuration
export NETWORK_MANAGER="NetworkManager"

# Display manager
export DISPLAY_MANAGER="gdm3"

# Firewall configuration
export ENABLE_UFW="yes"
export UFW_DEFAULT_POLICY="deny"

# Update settings
export ENABLE_AUTOMATIC_UPDATES="no"  # Managed manually
export UNATTENDED_UPGRADES="no"

# Logging
echo "$(date): FAI class UBUNTU_DESKTOP configured" >> $LOGDIR/class-assignment.log

# Set additional variables based on hardware detection
if [ -n "${FAI_HARDWARE_VENDOR:-}" ]; then
    echo "Hardware vendor detected: $FAI_HARDWARE_VENDOR"
    case "$FAI_HARDWARE_VENDOR" in
        dell)
            export HARDWARE_PACKAGES="dell-recovery dell-super-io-check"
            ;;
        lenovo)
            export HARDWARE_PACKAGES="thinkfan tp-smapi-dkms"
            ;;
        hp)
            export HARDWARE_PACKAGES="hplip hplip-gui"
            ;;
        *)
            export HARDWARE_PACKAGES=""
            ;;
    esac
fi

# Function to check if we're in a virtual machine
detect_virtualization() {
    if command -v systemd-detect-virt >/dev/null 2>&1; then
        VIRT=$(systemd-detect-virt)
        if [ "$VIRT" != "none" ]; then
            echo "VIRTUAL_MACHINE"
            export VIRTUALIZATION="$VIRT"
            export HARDWARE_PACKAGES="$HARDWARE_PACKAGES open-vm-tools"
        fi
    fi
}

# Detect virtualization
detect_virtualization

# Check if we need custom software class
if [ -n "${CUSTOM_PACKAGES:-}" ] || [ -n "${CUSTOM_DEB_URLS:-}" ]; then
    echo "CUSTOM_SOFTWARE"
fi

# Check for development tools requirement
if echo "${CUSTOM_PACKAGES:-}" | grep -E "(git|vim|code|build-essential|python.*pip|nodejs|npm)" >/dev/null 2>&1; then
    echo "DEVELOPMENT_TOOLS"
    export INSTALL_DEVELOPMENT="yes"
fi

# Security and hardening
if [ "${SECURITY_HARDENING:-no}" = "yes" ]; then
    echo "SECURITY_HARDENING"
    export INSTALL_SECURITY_TOOLS="yes"
fi

# Final validation
if [ -z "${FAI_DISTRIBUTION:-}" ]; then
    echo "ERROR: FAI_DISTRIBUTION not set" >&2
    exit 1
fi

echo "$(date): UBUNTU_DESKTOP class configuration completed" >> $LOGDIR/class-assignment.log