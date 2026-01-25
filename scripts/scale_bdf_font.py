#!/usr/bin/env python3
"""
Scale a BDF font file by a given factor.
Enlarges both the bitmap data and metadata.
"""

import sys
import re

def scale_bitmap(hex_rows, scale_factor):
    """
    Scale bitmap data by replicating each pixel scale_factor times.
    hex_rows: list of hex strings representing bitmap rows
    scale_factor: how many times to enlarge (e.g., 3 for 3x)
    """
    scaled_rows = []
    
    for hex_row in hex_rows:
        # Handle multiple bytes per row (for wider fonts)
        hex_bytes = [hex_row[i:i+2] for i in range(0, len(hex_row), 2)]
        
        # Convert to binary and expand horizontally
        binary = ''
        for hex_byte in hex_bytes:
            byte_val = int(hex_byte, 16)
            binary += format(byte_val, '08b')
        
        # Expand each bit horizontally
        expanded = ''
        for bit in binary:
            expanded += bit * scale_factor
        
        # Convert back to hex
        hex_bytes = []
        for i in range(0, len(expanded), 8):
            byte_str = expanded[i:i+8]
            if len(byte_str) < 8:
                byte_str = byte_str.ljust(8, '0')
            hex_bytes.append(format(int(byte_str, 2), '02x'))
        
        # Add this row multiple times (vertical scaling)
        for _ in range(scale_factor):
            scaled_rows.append(''.join(hex_bytes))
    
    return scaled_rows

def scale_bdf_font(input_file, output_file, scale_factor):
    """Scale a BDF font file by the given factor."""
    
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    output_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Scale header properties
        if line.startswith('SIZE '):
            parts = line.strip().split()
            size = int(parts[1])
            scaled_size = size * scale_factor
            output_lines.append(f'SIZE {scaled_size} {parts[2]} {parts[3]}\n')
        elif line.startswith('FONTBOUNDINGBOX '):
            parts = line.strip().split()
            width = int(parts[1]) * scale_factor
            height = int(parts[2]) * scale_factor
            x_offset = int(parts[3]) * scale_factor
            y_offset = int(parts[4]) * scale_factor
            output_lines.append(f'FONTBOUNDINGBOX {width} {height} {x_offset} {y_offset}\n')
        elif line.startswith('PIXEL_SIZE '):
            parts = line.strip().split()
            pixel_size = int(parts[1]) * scale_factor
            output_lines.append(f'PIXEL_SIZE {pixel_size}\n')
        elif line.startswith('POINT_SIZE '):
            parts = line.strip().split()
            point_size = int(parts[1]) * scale_factor
            output_lines.append(f'POINT_SIZE {point_size}\n')
        elif line.startswith('AVERAGE_WIDTH '):
            parts = line.strip().split()
            avg_width = int(parts[1]) * scale_factor
            output_lines.append(f'AVERAGE_WIDTH {avg_width}\n')
        elif line.startswith('DWIDTH '):
            parts = line.strip().split()
            width = int(parts[1]) * scale_factor
            height = int(parts[2]) if len(parts) > 2 else 0
            output_lines.append(f'DWIDTH {width} {height}\n')
        elif line.startswith('BBX '):
            parts = line.strip().split()
            width = int(parts[1]) * scale_factor
            height = int(parts[2]) * scale_factor
            x_offset = int(parts[3]) * scale_factor
            y_offset = int(parts[4]) * scale_factor
            output_lines.append(f'BBX {width} {height} {x_offset} {y_offset}\n')
        elif line.startswith('BITMAP'):
            output_lines.append(line)
            i += 1
            bitmap_rows = []
            
            # Collect bitmap rows until ENDCHAR
            while i < len(lines) and not lines[i].startswith('ENDCHAR'):
                bitmap_rows.append(lines[i].strip())
                i += 1
            
            # Scale the bitmap
            scaled_bitmap = scale_bitmap(bitmap_rows, scale_factor)
            for row in scaled_bitmap:
                output_lines.append(row + '\n')
            
            # Add ENDCHAR
            output_lines.append('ENDCHAR\n')
            i += 1
            continue
        else:
            output_lines.append(line)
        
        i += 1
    
    with open(output_file, 'w') as f:
        f.writelines(output_lines)
    
    print(f"Scaled font by {scale_factor}x saved to {output_file}")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <input_bdf> <output_bdf> <scale_factor>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    scale_factor = int(sys.argv[3])
    
    scale_bdf_font(input_file, output_file, scale_factor)
