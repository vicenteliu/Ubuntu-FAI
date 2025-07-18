#!/bin/bash
# FAI class script for hardware-specific configuration
# Detects hardware vendor and applies appropriate settings

# Set error handling
set -euo pipefail

# Hardware detection functions
detect_dell() {
    if dmidecode -s system-manufacturer 2>/dev/null | grep -qi "dell"; then
        echo "HARDWARE_DELL"
        export FAI_HARDWARE_VENDOR="dell"
        export HARDWARE_SPECIFIC_PACKAGES="dell-recovery dell-super-io-check"
        export HARDWARE_KERNEL_PARAMS="dell_laptop.force=1"
        export POWER_MANAGEMENT="dell"
        return 0
    fi
    return 1
}

detect_lenovo() {
    if dmidecode -s system-manufacturer 2>/dev/null | grep -qi "lenovo"; then
        echo "HARDWARE_LENOVO" 
        export FAI_HARDWARE_VENDOR="lenovo"
        export HARDWARE_SPECIFIC_PACKAGES="thinkfan tp-smapi-dkms"
        export HARDWARE_KERNEL_PARAMS="thinkpad_acpi.fan_control=1"
        export POWER_MANAGEMENT="thinkpad"
        
        # Detect ThinkPad models
        if dmidecode -s system-product-name 2>/dev/null | grep -qi "thinkpad"; then
            echo "THINKPAD"
            export THINKPAD_MODEL=$(dmidecode -s system-product-name 2>/dev/null || echo "unknown")
        fi
        return 0
    fi
    return 1
}

detect_hp() {
    if dmidecode -s system-manufacturer 2>/dev/null | grep -qi "hewlett.packard\|hp"; then
        echo "HARDWARE_HP"
        export FAI_HARDWARE_VENDOR="hp"
        export HARDWARE_SPECIFIC_PACKAGES="hplip hplip-gui"
        export HARDWARE_KERNEL_PARAMS=""
        export POWER_MANAGEMENT="generic"
        return 0
    fi
    return 1
}

detect_virtualization() {
    local virt_type=""
    
    # Check for common virtualization platforms
    if command -v systemd-detect-virt >/dev/null 2>&1; then
        virt_type=$(systemd-detect-virt 2>/dev/null || echo "none")
    fi
    
    if [ "$virt_type" != "none" ] && [ -n "$virt_type" ]; then
        echo "VIRTUALIZATION"
        echo "VIRTUAL_${virt_type^^}"
        export VIRTUALIZATION_TYPE="$virt_type"
        export VIRTUAL_MACHINE="yes"
        
        # Add virtualization-specific packages
        case "$virt_type" in
            vmware)
                export VIRTUAL_PACKAGES="open-vm-tools open-vm-tools-desktop"
                ;;
            kvm|qemu)
                export VIRTUAL_PACKAGES="qemu-guest-agent spice-vdagent"
                ;;
            virtualbox)
                export VIRTUAL_PACKAGES="virtualbox-guest-additions-iso"
                ;;
            xen)
                export VIRTUAL_PACKAGES="xe-guest-utilities"
                ;;
            *)
                export VIRTUAL_PACKAGES=""
                ;;
        esac
        
        # Virtual machines don't need hardware-specific power management
        export POWER_MANAGEMENT="virtual"
        return 0
    fi
    
    return 1
}

detect_cpu_vendor() {
    local cpu_vendor=""
    
    if [ -f /proc/cpuinfo ]; then
        cpu_vendor=$(grep -m1 "vendor_id" /proc/cpuinfo | cut -d: -f2 | xargs)
        
        case "$cpu_vendor" in
            "GenuineIntel")
                echo "CPU_INTEL"
                export CPU_VENDOR="intel"
                export CPU_MICROCODE_PACKAGE="intel-microcode"
                ;;
            "AuthenticAMD")
                echo "CPU_AMD"
                export CPU_VENDOR="amd"
                export CPU_MICROCODE_PACKAGE="amd64-microcode"
                ;;
            *)
                export CPU_VENDOR="unknown"
                export CPU_MICROCODE_PACKAGE=""
                ;;
        esac
    fi
}

detect_gpu_vendor() {
    local gpu_info=""
    
    if command -v lspci >/dev/null 2>&1; then
        gpu_info=$(lspci | grep -i "vga\|3d\|display" || true)
        
        if echo "$gpu_info" | grep -qi "nvidia"; then
            echo "GPU_NVIDIA"
            export GPU_VENDOR="nvidia"
            export GPU_DRIVER_PACKAGE="nvidia-driver-535"  # LTS driver
        elif echo "$gpu_info" | grep -qi "amd\|ati"; then
            echo "GPU_AMD"
            export GPU_VENDOR="amd"
            export GPU_DRIVER_PACKAGE="xserver-xorg-video-amdgpu"
        elif echo "$gpu_info" | grep -qi "intel"; then
            echo "GPU_INTEL"
            export GPU_VENDOR="intel"
            export GPU_DRIVER_PACKAGE="xserver-xorg-video-intel"
        fi
    fi
}

detect_network_hardware() {
    local wifi_detected="no"
    local ethernet_detected="no"
    
    if command -v lspci >/dev/null 2>&1; then
        # Check for WiFi
        if lspci | grep -qi "wireless\|wifi\|802.11"; then
            echo "WIFI_HARDWARE"
            wifi_detected="yes"
            export WIFI_PACKAGES="wireless-tools wpasupplicant"
        fi
        
        # Check for Ethernet
        if lspci | grep -qi "ethernet"; then
            echo "ETHERNET_HARDWARE"
            ethernet_detected="yes"
        fi
        
        # Check for Broadcom WiFi (often needs special drivers)
        if lspci | grep -qi "broadcom.*wireless"; then
            echo "WIFI_BROADCOM"
            export WIFI_PACKAGES="$WIFI_PACKAGES broadcom-sta-dkms"
        fi
    fi
    
    export NETWORK_WIFI="$wifi_detected"
    export NETWORK_ETHERNET="$ethernet_detected"
}

detect_storage_type() {
    local has_ssd="no"
    local has_nvme="no"
    
    # Check for NVMe drives
    if [ -d /sys/class/nvme ] && [ -n "$(ls -A /sys/class/nvme 2>/dev/null)" ]; then
        echo "STORAGE_NVME"
        has_nvme="yes"
        export NVME_PACKAGES="nvme-cli"
    fi
    
    # Check for SSDs
    for disk in /sys/block/sd*; do
        if [ -f "$disk/queue/rotational" ] && [ "$(cat "$disk/queue/rotational")" = "0" ]; then
            echo "STORAGE_SSD"
            has_ssd="yes"
            break
        fi
    done
    
    export STORAGE_HAS_SSD="$has_ssd"
    export STORAGE_HAS_NVME="$has_nvme"
    
    # Enable SSD optimizations if SSD detected
    if [ "$has_ssd" = "yes" ] || [ "$has_nvme" = "yes" ]; then
        export SSD_OPTIMIZATIONS="yes"
        export MOUNT_OPTIONS="noatime,discard"
    fi
}

# Main hardware detection logic
main() {
    echo "$(date): Starting hardware detection" >> $LOGDIR/hardware-detection.log
    
    # Try hardware vendor detection in order of specificity
    if ! detect_virtualization; then
        # Only detect physical hardware if not virtual
        detect_dell || detect_lenovo || detect_hp || {
            echo "HARDWARE_GENERIC"
            export FAI_HARDWARE_VENDOR="generic"
            export HARDWARE_SPECIFIC_PACKAGES=""
        }
    fi
    
    # Always detect CPU, GPU, and other components
    detect_cpu_vendor
    detect_gpu_vendor
    detect_network_hardware
    detect_storage_type
    
    # Log detected hardware
    {
        echo "=== Hardware Detection Results ==="
        echo "Vendor: ${FAI_HARDWARE_VENDOR:-unknown}"
        echo "CPU: ${CPU_VENDOR:-unknown}"
        echo "GPU: ${GPU_VENDOR:-unknown}"
        echo "Virtualization: ${VIRTUALIZATION_TYPE:-none}"
        echo "WiFi: ${NETWORK_WIFI:-unknown}"
        echo "SSD: ${STORAGE_HAS_SSD:-unknown}"
        echo "NVMe: ${STORAGE_HAS_NVME:-unknown}"
        echo "=================================="
    } >> $LOGDIR/hardware-detection.log
    
    # Export combined package list
    local all_packages=""
    
    # Add hardware-specific packages
    if [ -n "${HARDWARE_SPECIFIC_PACKAGES:-}" ]; then
        all_packages="$all_packages $HARDWARE_SPECIFIC_PACKAGES"
    fi
    
    # Add CPU microcode
    if [ -n "${CPU_MICROCODE_PACKAGE:-}" ]; then
        all_packages="$all_packages $CPU_MICROCODE_PACKAGE"
    fi
    
    # Add GPU drivers
    if [ -n "${GPU_DRIVER_PACKAGE:-}" ]; then
        all_packages="$all_packages $GPU_DRIVER_PACKAGE"
    fi
    
    # Add WiFi packages
    if [ -n "${WIFI_PACKAGES:-}" ]; then
        all_packages="$all_packages $WIFI_PACKAGES"
    fi
    
    # Add virtualization packages
    if [ -n "${VIRTUAL_PACKAGES:-}" ]; then
        all_packages="$all_packages $VIRTUAL_PACKAGES"
    fi
    
    # Add NVMe tools
    if [ -n "${NVME_PACKAGES:-}" ]; then
        all_packages="$all_packages $NVME_PACKAGES"
    fi
    
    # Export final package list (remove duplicates and trim whitespace)
    export HARDWARE_PACKAGES=$(echo "$all_packages" | tr ' ' '\n' | sort -u | tr '\n' ' ' | xargs)
    
    echo "$(date): Hardware detection completed. Packages: $HARDWARE_PACKAGES" >> $LOGDIR/hardware-detection.log
}

# Execute main function
main