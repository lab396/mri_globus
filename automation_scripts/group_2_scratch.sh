#!/bin/bash

# Source directory containing user ID directories
SOURCE_DIR="/storage/group/MCL/default/globus-share"
DEST_ROOT="/storage/group"
ORPHAN_DIR="$DEST_ROOT/MCL/default/orphan"
DATE=$(date +"%Y%m%d%H%M")

for user_dir in "$SOURCE_DIR"/*; do
    if [ -d "$user_dir" ]; then
        userid=$(basename "$user_dir")
        dest_path="$DEST_ROOT/$userid"
        
        if [ -d "$dest_path" ]; then
            # If the destination directory exists, copy to its 'default' subdirectory
            mkdir -p "$dest_path/default/$DATE"
            cp -r "$user_dir" "$dest_path/default/$DATE"
            echo "Copied $user_dir to $dest_path/default/$DATE"
        else
            # Check if the user's scratch directory exists
            SCRATCH_DIR="/scratch/$userid"
            if [ -d "$SCRATCH_DIR" ]; then
                mkdir -p "$SCRATCH_DIR/$DATE"
                cp -r "$user_dir" "$SCRATCH_DIR/$DATE"
                echo "Copied $user_dir to $SCRATCH_DIR/$DATE"
            else
                # If neither destination nor scratch exists, copy to orphan directory
                cp -r "$user_dir" "$ORPHAN_DIR/"
                echo "Copied $user_dir to $ORPHAN_DIR/"
            fi
        fi
    fi
done

