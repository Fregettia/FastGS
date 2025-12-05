#!/usr/bin/env python3
"""
Multiprocess JPG Image Resizer
Resize all JPG images in a folder using multiple CPU cores

Usage Examples:
  # Resize by percentage (maintains aspect ratio)
  python resizetool.py -i ./photos -o ./resized --percent 75
  
  # Resize to specific width (height auto-calculated to maintain aspect ratio)
  python resizetool.py -i ./photos -o ./resized --width 1920
  
  # Resize to specific height (width auto-calculated to maintain aspect ratio)
  python resizetool.py -i ./photos -o ./resized --height 1080
  
  # Resize to exact dimensions (no aspect ratio preservation)
  python resizetool.py -i ./photos -o ./resized --width 1920 --height 1080 --exact
  
  # Fit within bounds (maintains aspect ratio, won't exceed width or height)
  python resizetool.py -i ./photos -o ./resized --width 1920 --height 1080 --aspect
  
  # Use multiple workers for faster processing
  python resizetool.py -i ./photos -o ./resized --width 1920 --workers 8

"""

import os
import argparse
from pathlib import Path
from multiprocessing import Pool, cpu_count
from PIL import Image


def resize_image(args):
    """
    Resize a single image file
    
    Args:
        args: tuple of (input_path, output_path, width, height, percent, maintain_aspect, exact)
    
    Returns:
        str: Status message
    """
    input_path, output_path, width, height, percent, maintain_aspect, exact = args
    
    try:
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (handles RGBA, etc.)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            original_width, original_height = img.size
            
            # Calculate dimensions based on percentage if specified
            if percent:
                width = int(original_width * percent / 100)
                height = int(original_height * percent / 100)
                resized = img.resize((width, height), Image.Resampling.LANCZOS)
            
            # Exact dimensions mode - resize to exact width x height (no aspect ratio)
            elif exact:
                resized = img.resize((width, height), Image.Resampling.LANCZOS)
            
            # Single dimension mode - calculate the other dimension to maintain aspect ratio
            elif width and not height:
                # Only width specified, calculate height
                aspect_ratio = original_height / original_width
                height = int(width * aspect_ratio)
                resized = img.resize((width, height), Image.Resampling.LANCZOS)
            
            elif height and not width:
                # Only height specified, calculate width
                aspect_ratio = original_width / original_height
                width = int(height * aspect_ratio)
                resized = img.resize((width, height), Image.Resampling.LANCZOS)
            
            # Maintain aspect ratio mode - fit within width x height bounds
            elif maintain_aspect:
                img.thumbnail((width, height), Image.Resampling.LANCZOS)
                resized = img
                width, height = resized.size  # Get actual dimensions after thumbnail
            
            # Default: exact dimensions
            else:
                resized = img.resize((width, height), Image.Resampling.LANCZOS)
            
            # Save the resized image
            resized.save(output_path, 'JPEG', quality=95)
            return f"✓ Resized: {os.path.basename(input_path)} ({original_width}x{original_height} → {width}x{height})"
    
    except Exception as e:
        return f"✗ Error with {os.path.basename(input_path)}: {str(e)}"


def get_image_files(input_folder):
    """Get all JPG/JPEG files from input folder"""
    extensions = {'.jpg', '.jpeg', '.JPG', '.JPEG'}
    image_files = []
    
    for file in os.listdir(input_folder):
        if Path(file).suffix in extensions:
            image_files.append(file)
    
    return image_files


def main():
    parser = argparse.ArgumentParser(
        description='Resize JPG images using multiprocessing'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input folder containing JPG images'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output folder for resized images'
    )
    parser.add_argument(
        '--percent', '-p',
        type=float,
        default=None,
        help='Resize by percentage (e.g., 50 for 50%% of original size)'
    )
    parser.add_argument(
        '--width', '-w',
        type=int,
        default=None,
        help='Target width in pixels (if only width specified, height auto-calculated to maintain aspect ratio)'
    )
    parser.add_argument(
        '--height', '-H',
        type=int,
        default=None,
        help='Target height in pixels (if only height specified, width auto-calculated to maintain aspect ratio)'
    )
    parser.add_argument(
        '--exact',
        action='store_true',
        help='Resize to exact width x height (ignores aspect ratio, requires both --width and --height)'
    )
    parser.add_argument(
        '--aspect',
        action='store_true',
        help='Maintain aspect ratio - fit within width x height bounds (requires both --width and --height)'
    )
    parser.add_argument(
        '--workers', '-n',
        type=int,
        default=None,
        help=f'Number of worker processes (default: {cpu_count()})'
    )
    
    args = parser.parse_args()
    
    # Validate input folder
    if not os.path.exists(args.input):
        print(f"Error: Input folder '{args.input}' does not exist")
        return
    
    # Validate arguments
    if args.percent is not None and args.percent <= 0:
        print("Error: Percentage must be greater than 0")
        return
    
    # Check that at least one resize method is specified
    if args.percent is None and args.width is None and args.height is None:
        print("Error: Must specify either --percent, --width, --height, or both --width and --height")
        return
    
    # Validate exact and aspect flags
    if args.exact and args.aspect:
        print("Error: Cannot use both --exact and --aspect flags")
        return
    
    if (args.exact or args.aspect) and (args.width is None or args.height is None):
        print("Error: --exact and --aspect flags require both --width and --height")
        return
    
    # Validate width and height values
    if args.width is not None and args.width <= 0:
        print("Error: Width must be greater than 0")
        return
    
    if args.height is not None and args.height <= 0:
        print("Error: Height must be greater than 0")
        return
    
    # Create output folder if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Get all image files
    image_files = get_image_files(args.input)
    
    if not image_files:
        print("No JPG images found in input folder")
        return
    
    print(f"Found {len(image_files)} images")
    
    # Display resize mode
    if args.percent:
        print(f"Mode: Resize to {args.percent}% of original size")
    elif args.exact:
        print(f"Mode: Exact dimensions (no aspect ratio preservation)")
        print(f"Target: {args.width}x{args.height}")
    elif args.aspect:
        print(f"Mode: Fit within bounds (maintain aspect ratio)")
        print(f"Maximum: {args.width}x{args.height}")
    elif args.width and not args.height:
        print(f"Mode: Resize to width {args.width}px (height auto-calculated)")
    elif args.height and not args.width:
        print(f"Mode: Resize to height {args.height}px (width auto-calculated)")
    else:
        print(f"Mode: Resize to exact dimensions")
        print(f"Target: {args.width}x{args.height}")
    
    # Determine number of workers
    num_workers = args.workers if args.workers else cpu_count()
    print(f"Using {num_workers} worker processes\n")
    
    # Prepare arguments for each image
    tasks = [
        (
            os.path.join(args.input, filename),
            os.path.join(args.output, filename),
            args.width,
            args.height,
            args.percent,
            args.aspect,
            args.exact
        )
        for filename in image_files
    ]
    
    # Process images using multiprocessing
    with Pool(processes=num_workers) as pool:
        results = pool.map(resize_image, tasks)
    
    # Print results
    print("\nResults:")
    for result in results:
        print(result)
    
    print(f"\nCompleted! Resized images saved to '{args.output}'")


if __name__ == '__main__':
    main()
