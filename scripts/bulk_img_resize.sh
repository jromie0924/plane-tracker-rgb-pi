#!/bin/bash

# Check if required arguments are provided
if [ $# -lt 4 ]; then
    echo "Error: Missing required arguments"
    echo "Usage: $0 <input_directory> <output_directory> <size> <file_type>"
    echo "Example: $0 input_images output_images 16 png"
    exit 1
fi

input_directory=$1
output_directory=$2
size=$3
file_type=$4

# Validate input directory exists
if [ ! -d "$input_directory" ]; then
    echo "Error: Input directory '$input_directory' does not exist"
    exit 1
fi

# Create output directory if it doesn't exist
if [ ! -d "$output_directory" ]; then
    echo "Creating output directory: $output_directory"
    mkdir -p "$output_directory"
fi

# Check if imagemagick is installed
if ! command -v magick &> /dev/null; then
    echo "Error: ImageMagick 'magick' command not found. Please install ImageMagick."
    exit 1
fi

# Process images
found_files=0
for img in "$input_directory"/*."$file_type"; do
    # Check if glob matched any files
    if [ ! -e "$img" ]; then
        continue
    fi
    
    found_files=1
    echo "Processing: $(basename "$img")"
    magick "$img" -resize "${size}x${size}" -background white -gravity center -extent "${size}x${size}" "$output_directory/$(basename "$img")"
done

if [ $found_files -eq 0 ]; then
    echo "Warning: No .$file_type files found in $input_directory"
    exit 1
fi

echo "Done! Images resized to ${size}x${size} in $output_directory"