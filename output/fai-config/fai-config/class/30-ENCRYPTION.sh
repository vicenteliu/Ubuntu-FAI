#!/bin/bash
# FAI class script for LUKS encryption configuration
# Handles LUKS full-disk encryption with LVM setup

# Set error handling
set -euo pipefail

# Check if encryption is enabled
if [ "${FAI_ENCRYPTION_ENABLED:-false}" != "true" ]; then
    echo "$(date): Encryption not enabled, skipping encryption configuration" >> $LOGDIR/encryption.log
    exit 0
fi

# Define encryption class
echo "UBUNTU_ENCRYPTED"

# LUKS encryption settings
export LUKS_ENABLED="yes"
export LUKS_CIPHER="${LUKS_CIPHER:-aes-xts-plain64}"
export LUKS_KEY_SIZE="${LUKS_KEY_SIZE:-512}"
export LUKS_HASH="${LUKS_HASH:-sha256}"
export LUKS_ITER_TIME="${LUKS_ITER_TIME:-2000}"

# LVM settings for encrypted setup
export LVM_ENABLED="yes"
export LVM_VG_NAME="ubuntu-vg"
export LVM_ROOT_SIZE="50%"
export LVM_HOME_SIZE="40%"
export LVM_SWAP_SIZE="8%"
export LVM_FREE_SIZE="2%"  # Keep some free space

# Partition layout for encrypted disk
export DISK_LAYOUT="encrypted_lvm"
export BOOT_PARTITION_SIZE="1G"
export EFI_PARTITION_SIZE="512M"

# File system settings
export ROOT_FILESYSTEM="ext4"
export HOME_FILESYSTEM="ext4"
export BOOT_FILESYSTEM="ext4"
export EFI_FILESYSTEM="vfat"

# Mount options for encrypted filesystems
export ROOT_MOUNT_OPTIONS="defaults,errors=remount-ro"
export HOME_MOUNT_OPTIONS="defaults,nodev,nosuid"

# Hardware-specific encryption optimizations
setup_encryption_for_hardware() {
    local vendor="${FAI_HARDWARE_VENDOR:-generic}"
    
    case "$vendor" in
        dell)
            # Dell-specific optimizations
            echo "LUKS_DELL_OPTIMIZED"
            export LUKS_KEY_SIZE="256"  # Better compatibility
            export LUKS_CIPHER="aes-xts-plain64"
            export LUKS_ALIGN="1024"  # Align to 1MB for Dell SSDs
            ;;
        lenovo)
            # Lenovo ThinkPad optimizations
            echo "LUKS_LENOVO_OPTIMIZED"
            if [ "${THINKPAD_MODEL:-}" != "" ]; then
                echo "LUKS_THINKPAD"
                # ThinkPad-specific encryption settings
                export LUKS_ALLOW_DISCARDS="yes"  # For SSD TRIM support
            fi
            ;;
        hp)
            # HP-specific optimizations
            echo "LUKS_HP_OPTIMIZED"
            # Avoid serpent cipher on HP hardware for performance
            if [ "$LUKS_CIPHER" = "serpent-xts-plain64" ]; then
                export LUKS_CIPHER="aes-xts-plain64"
                echo "$(date): WARNING: Changed cipher from serpent to aes for HP compatibility" >> $LOGDIR/encryption.log
            fi
            ;;
        *)
            echo "LUKS_GENERIC"
            ;;
    esac
}

# SSD-specific encryption settings
setup_encryption_for_ssd() {
    if [ "${STORAGE_HAS_SSD:-no}" = "yes" ] || [ "${STORAGE_HAS_NVME:-no}" = "yes" ]; then
        echo "LUKS_SSD_OPTIMIZED"
        
        # Enable TRIM support for SSDs
        export LUKS_ALLOW_DISCARDS="yes"
        export SSD_MOUNT_OPTIONS="noatime,discard"
        
        # Optimize for SSD alignment
        export LUKS_ALIGN="1024"  # 1MB alignment
        
        # Reduce writes for SSD longevity
        export REDUCE_WRITES="yes"
        
        echo "$(date): Configured LUKS for SSD optimization" >> $LOGDIR/encryption.log
    fi
}

# Virtual machine encryption settings
setup_encryption_for_vm() {
    if [ "${VIRTUAL_MACHINE:-no}" = "yes" ]; then
        echo "LUKS_VIRTUAL_MACHINE"
        
        # VM-specific optimizations
        export LUKS_CIPHER="aes-xts-plain64"  # Best performance in VMs
        export LUKS_KEY_SIZE="256"  # Faster decryption
        
        # Reduce iteration time for VMs
        export LUKS_ITER_TIME="1000"
        
        echo "$(date): Configured LUKS for virtual machine" >> $LOGDIR/encryption.log
    fi
}

# Validate encryption parameters
validate_encryption_settings() {
    local errors=0
    
    # Validate cipher
    case "$LUKS_CIPHER" in
        aes-xts-plain64|aes-cbc-essiv:sha256|aes-lrw-benbi|serpent-xts-plain64|twofish-xts-plain64)
            ;;
        *)
            echo "ERROR: Invalid LUKS cipher: $LUKS_CIPHER" >&2
            errors=$((errors + 1))
            ;;
    esac
    
    # Validate key size
    case "$LUKS_KEY_SIZE" in
        256|512)
            ;;
        *)
            echo "ERROR: Invalid LUKS key size: $LUKS_KEY_SIZE" >&2
            errors=$((errors + 1))
            ;;
    esac
    
    # Validate hash
    case "$LUKS_HASH" in
        sha1|sha256|sha512|ripemd160)
            ;;
        *)
            echo "ERROR: Invalid LUKS hash: $LUKS_HASH" >&2
            errors=$((errors + 1))
            ;;
    esac
    
    if [ $errors -gt 0 ]; then
        echo "ERROR: $errors encryption validation errors found" >&2
        exit 1
    fi
    
    echo "$(date): Encryption settings validation passed" >> $LOGDIR/encryption.log
}

# Setup initramfs for encryption
setup_initramfs() {
    echo "INITRAMFS_ENCRYPTION"
    
    # Required packages for encryption support
    export ENCRYPTION_PACKAGES="cryptsetup cryptsetup-initramfs lvm2"
    
    # Initramfs modules
    export INITRAMFS_MODULES="aes aes_x86_64 aes-xts dm-crypt dm-mod lvm"
    
    # GRUB settings for encrypted boot
    export GRUB_ENABLE_CRYPTODISK="y"
    export GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"
    
    echo "$(date): Configured initramfs for encryption" >> $LOGDIR/encryption.log
}

# Performance tuning for encrypted filesystems
setup_encryption_performance() {
    echo "LUKS_PERFORMANCE_TUNED"
    
    # Crypto API optimization
    export CRYPTO_FIPS_MODE="0"  # Disable FIPS mode for performance
    
    # I/O scheduler optimization for encrypted storage
    if [ "${STORAGE_HAS_SSD:-no}" = "yes" ] || [ "${STORAGE_HAS_NVME:-no}" = "yes" ]; then
        export IO_SCHEDULER="mq-deadline"
    else
        export IO_SCHEDULER="cfq"
    fi
    
    # Memory optimization
    export CRYPTO_THREADS="auto"  # Let kernel decide optimal thread count
    
    echo "$(date): Applied encryption performance optimizations" >> $LOGDIR/encryption.log
}

# Backup and recovery setup
setup_encryption_recovery() {
    echo "LUKS_RECOVERY_SETUP"
    
    # Enable LUKS header backup
    export LUKS_HEADER_BACKUP="yes"
    export LUKS_BACKUP_DIR="/boot/luks-headers"
    
    # Recovery boot options
    export GRUB_RECOVERY_ENCRYPTION="yes"
    
    echo "$(date): Configured encryption recovery options" >> $LOGDIR/encryption.log
}

# Main encryption configuration
main() {
    echo "$(date): Starting LUKS encryption configuration" >> $LOGDIR/encryption.log
    
    # Validate settings first
    validate_encryption_settings
    
    # Apply hardware-specific optimizations
    setup_encryption_for_hardware
    
    # Apply storage-specific optimizations  
    setup_encryption_for_ssd
    
    # Apply virtualization optimizations
    setup_encryption_for_vm
    
    # Setup supporting components
    setup_initramfs
    setup_encryption_performance
    setup_encryption_recovery
    
    # Log final configuration
    {
        echo "=== LUKS Encryption Configuration ==="
        echo "Cipher: $LUKS_CIPHER"
        echo "Key Size: $LUKS_KEY_SIZE bits"
        echo "Hash: $LUKS_HASH"
        echo "Iteration Time: $LUKS_ITER_TIME ms"
        echo "Allow Discards: ${LUKS_ALLOW_DISCARDS:-no}"
        echo "Alignment: ${LUKS_ALIGN:-default}"
        echo "Hardware Vendor: ${FAI_HARDWARE_VENDOR:-generic}"
        echo "Storage Type: SSD=${STORAGE_HAS_SSD:-no}, NVMe=${STORAGE_HAS_NVME:-no}"
        echo "Virtual Machine: ${VIRTUAL_MACHINE:-no}"
        echo "===================================="
    } >> $LOGDIR/encryption.log
    
    # Export all encryption packages
    local all_packages="$ENCRYPTION_PACKAGES"
    
    # Add hardware-specific encryption packages if any
    if [ -n "${HARDWARE_ENCRYPTION_PACKAGES:-}" ]; then
        all_packages="$all_packages $HARDWARE_ENCRYPTION_PACKAGES"
    fi
    
    export ENCRYPTION_PACKAGES="$all_packages"
    
    echo "$(date): LUKS encryption configuration completed" >> $LOGDIR/encryption.log
}

# Execute main function
main