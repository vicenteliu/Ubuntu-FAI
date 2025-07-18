#!/bin/bash
# First-boot script for Ubuntu FAI custom installation
# Auto-generated from configuration

set -euo pipefail

# Logging setup
LOGFILE="/var/log/first-boot.log"
exec 1> >(tee -a "$LOGFILE")
exec 2>&1

echo "==============================================="
echo "Ubuntu FAI First Boot Script Starting"
echo "Date: $(date)"
echo "==============================================="

# Color output functions
log_info() {
    echo -e "\033[32m[INFO]\033[0m $1"
}

log_warning() {
    echo -e "\033[33m[WARNING]\033[0m $1"
}

log_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

# Error handling
handle_error() {
    log_error "Script failed at line $1"
    exit 1
}
trap 'handle_error $LINENO' ERR

# Wait for system to be ready
log_info "Waiting for system to be ready..."
sleep 30

# Update package lists
log_info "Updating package lists..."
apt-get update




# Hardware-specific configurations
log_info "Applying hardware-specific configurations for HardwareVendor.DELL"

case "dell" in
    "dell")
        log_info "Applying Dell-specific optimizations..."
        # Dell Command Configure if available
        if command -v cctk &> /dev/null; then
            cctk --ThermalManagement=Optimized || true
        fi
        ;;
    "lenovo")
        log_info "Applying Lenovo-specific optimizations..."
        # Lenovo-specific power management
        echo 'SUBSYSTEM=="power_supply", ATTR{online}=="0", RUN+="/usr/bin/x86_energy_perf_policy performance"' > /etc/udev/rules.d/50-lenovo-power.rules
        ;;
    "hp")
        log_info "Applying HP-specific optimizations..."
        # HP-specific configurations
        modprobe hp_wmi || true
        ;;
esac


# Run custom scripts

# System cleanup and optimization
log_info "Performing system cleanup..."

# Clean package cache
apt-get autoremove -y
apt-get autoclean

# Update locate database
updatedb || true

# Generate SSH host keys if missing
ssh-keygen -A || true

# Set proper permissions
chmod 600 /etc/ssh/ssh_host_*_key
chmod 644 /etc/ssh/ssh_host_*_key.pub

# LUKS/encryption specific configurations
log_info "Configuring encryption settings..."

# Update initramfs to include encryption modules
update-initramfs -u

# Configure crypttab if needed
if [ -f /etc/crypttab ]; then
    log_info "Crypttab configuration found"
fi

# Final system configuration
log_info "Applying final system configurations..."

# Set timezone

# Disable first-boot service (this script)
systemctl disable first-boot.service

# Create completion marker
touch /var/lib/first-boot-completed
echo "$(date): First boot configuration completed" > /var/lib/first-boot-completed

echo "==============================================="
echo "Ubuntu FAI First Boot Script Completed"
echo "Date: $(date)"
echo "==============================================="

log_info "First-boot configuration completed successfully!"
log_info "System will reboot in 10 seconds..."

# Schedule reboot
sleep 10
reboot