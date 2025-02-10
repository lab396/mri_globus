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
            # If the destination directory does not exist, copy to orphan directory
            cp -r "$user_dir" "$ORPHAN_DIR/"
            echo "Copied $user_dir to $ORPHAN_DIR/"
        fi
    fi
done
