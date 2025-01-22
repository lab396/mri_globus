#!/bin/bash

# Set Globus endpoint UUIDs
SOURCE_ENDPOINT="YOUR_SOURCE_ENDPOINT_UUID"
DESTINATION_ENDPOINT="YOUR_DESTINATION_ENDPOINT_UUID"

# Set source and destination paths
SOURCE_PATH="/storage/long/"
DESTINATION_PATH="/storage/group/MCL/default/globus-share/"

# Check if Globus CLI is installed
if ! command -v globus &> /dev/null; then
    echo "Globus CLI is not installed. Please install it and try again."
    exit 1
fi

# Authenticate with Globus
globus login

# Perform the transfer
echo "Starting transfer..."
TRANSFER_ID=$(globus transfer --recursive "$SOURCE_ENDPOINT:$SOURCE_PATH" "$DESTINATION_ENDPOINT:$DESTINATION_PATH" --notify off)

# Wait for transfer to complete
echo "Waiting for transfer to complete (Task ID: $TRANSFER_ID)..."
globus task wait "$TRANSFER_ID"

# Check transfer status
if [ $? -eq 0 ]; then
    echo "Transfer completed successfully!"
else
    echo "Transfer failed. Please check the logs for details."
fi
