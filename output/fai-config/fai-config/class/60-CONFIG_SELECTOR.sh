#!/bin/bash
# Configuration selector based on encryption settings
# Generated automatically

if [ "${FAI_ENCRYPTION_ENABLED:-false}" = "true" ]; then
    echo "UBUNTU_ENCRYPTED"
    echo "Using encrypted disk configuration"
else
    echo "UBUNTU_DESKTOP"  
    echo "Using standard disk configuration"
fi

# Log configuration selection
echo "$(date): Configuration selector applied" >> $LOGDIR/config-selector.log
