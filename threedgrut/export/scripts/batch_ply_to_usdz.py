# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import sys
import logging
from pathlib import Path
from typing import List, Tuple
import concurrent.futures
import threading
from dataclasses import dataclass

from hydra.compose import compose
from hydra.initialize import initialize
from omegaconf import DictConfig

from threedgrut.export.usdz_exporter import USDZExporter
from threedgrut.model.model import MixtureOfGaussians

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Thread-local storage for model and exporter to avoid recreation
thread_local = threading.local()

@dataclass
class ConversionTask:
    """Represents a single PLY to USDZ conversion task."""
    input_path: Path
    output_path: Path
    relative_path: Path  # Relative path from input root for logging


def load_default_config(
    config_name: str = 'apps/colmap_3dgut.yaml',
    config_path: str = '../../../configs'
) -> DictConfig:
    """
    Load configuration using Hydra from the specified config file.

    Args:
        config_name: Name of the configuration YAML file to load
        config_path: Path to the configuration directory

    Returns:
        The loaded configuration object
    """
    with initialize(version_base=None, config_path=config_path):
        conf = compose(config_name=config_name)
    return conf


def find_ply_files(input_dir: Path) -> List[Path]:
    """
    Recursively find all PLY files in the input directory.

    Args:
        input_dir: Directory to search for PLY files

    Returns:
        List of PLY file paths
    """
    ply_files = []
    for ply_file in input_dir.rglob("*.ply"):
        if ply_file.is_file():
            ply_files.append(ply_file)
    
    logger.info(f"Found {len(ply_files)} PLY files in {input_dir}")
    return ply_files


def create_conversion_tasks(ply_files: List[Path], input_dir: Path, output_dir: Path) -> List[ConversionTask]:
    """
    Create conversion tasks maintaining directory structure.

    Args:
        ply_files: List of PLY file paths
        input_dir: Input root directory
        output_dir: Output root directory

    Returns:
        List of conversion tasks
    """
    tasks = []
    for ply_file in ply_files:
        # Calculate relative path from input directory
        relative_path = ply_file.relative_to(input_dir)
        
        # Create output path with same directory structure but .usdz extension
        output_path = output_dir / relative_path.with_suffix('.usdz')
        
        tasks.append(ConversionTask(
            input_path=ply_file,
            output_path=output_path,
            relative_path=relative_path
        ))
    
    return tasks


def get_thread_local_objects(force_zero_order_sh: bool):
    """
    Get or create thread-local model and exporter objects.
    This avoids recreating these objects for each conversion in the same thread.
    """
    if not hasattr(thread_local, 'model') or not hasattr(thread_local, 'exporter'):
        # Load configuration
        conf = load_default_config()
        
        # Configure for zero-order SH if requested
        if force_zero_order_sh:
            conf.model.progressive_training.max_n_features = 0
            conf.model.progressive_training.init_n_features = 0
            conf.render.particle_radiance_sph_degree = 0
        
        # Create model and exporter
        thread_local.model = MixtureOfGaussians(conf)
        thread_local.exporter = USDZExporter()
        thread_local.conf = conf
        thread_local.force_zero_order_sh = force_zero_order_sh
    
    return thread_local.model, thread_local.exporter, thread_local.conf


def convert_single_file(task: ConversionTask, force_zero_order_sh: bool) -> Tuple[bool, str]:
    """
    Convert a single PLY file to USDZ.

    Args:
        task: Conversion task containing input/output paths
        force_zero_order_sh: Whether to force zero-order spherical harmonics

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Get thread-local objects
        model, exporter, conf = get_thread_local_objects(force_zero_order_sh)
        
        # Create output directory
        task.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load PLY file
        if force_zero_order_sh:
            model.init_from_ply_zero_order_sh(str(task.input_path), init_model=False)
        else:
            model.init_from_ply(str(task.input_path), init_model=False)
        
        # Export to USDZ
        exporter.export(model, task.output_path, dataset=None, conf=conf)
        
        return True, f"✅ {task.relative_path} -> {task.output_path.name}"
        
    except Exception as e:
        import traceback
        error_msg = f"❌ {task.relative_path}: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False, error_msg


def main():
    # Add CUDA DLL directories to help with loading extensions
    import os
    cuda_paths = [
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.5\bin",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0\bin",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.7\bin"
    ]
    for cuda_path in cuda_paths:
        if os.path.exists(cuda_path):
            try:
                os.add_dll_directory(cuda_path)
                logger.info(f"Added CUDA DLL directory: {cuda_path}")
            except (OSError, AttributeError):
                # add_dll_directory might not be available on all systems
                pass

    parser = argparse.ArgumentParser(
        description="Batch convert PLY files to USDZ format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert all PLY files in input_folder to output_folder
  python batch_ply_to_usdz.py input_folder output_folder

  # Use 4 parallel workers
  python batch_ply_to_usdz.py input_folder output_folder --workers 4

  # Force zero-order spherical harmonics for Isaac Sim compatibility
  python batch_ply_to_usdz.py input_folder output_folder --force_zero_order_sh
        """
    )
    
    parser.add_argument("input_dir", type=str, 
                        help="Input directory containing PLY files (searched recursively)")
    parser.add_argument("output_dir", type=str,
                        help="Output directory for USDZ files (directory structure will be preserved)")
    parser.add_argument("--workers", type=int, default=1,
                        help="Number of parallel workers (default: 1)")
    parser.add_argument("--force_zero_order_sh", action="store_true", default=True,
                        help="Force conversion to 0-order spherical harmonics for Isaac Sim 5.0 compatibility (default: True)")
    parser.add_argument("--dry_run", action="store_true",
                        help="Show what would be converted without actually converting")

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    # Validate input directory
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        sys.exit(1)

    if not input_dir.is_dir():
        logger.error(f"Input path is not a directory: {input_dir}")
        sys.exit(1)

    # Find all PLY files
    ply_files = find_ply_files(input_dir)
    if not ply_files:
        logger.warning(f"No PLY files found in {input_dir}")
        sys.exit(0)

    # Create conversion tasks
    tasks = create_conversion_tasks(ply_files, input_dir, output_dir)

    logger.info(f"Planning to convert {len(tasks)} files")
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Workers: {args.workers}")
    logger.info(f"Force zero-order SH: {args.force_zero_order_sh}")

    if args.dry_run:
        logger.info("\n=== DRY RUN - No files will be converted ===")
        for task in tasks:
            logger.info(f"Would convert: {task.relative_path} -> {task.output_path.relative_to(output_dir)}")
        sys.exit(0)

    # Perform conversions
    successful_conversions = 0
    failed_conversions = 0

    if args.workers == 1:
        # Single-threaded processing
        for i, task in enumerate(tasks, 1):
            logger.info(f"[{i}/{len(tasks)}] Converting {task.relative_path}")
            success, message = convert_single_file(task, args.force_zero_order_sh)
            logger.info(message)
            
            if success:
                successful_conversions += 1
            else:
                failed_conversions += 1
    else:
        # Multi-threaded processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(convert_single_file, task, args.force_zero_order_sh): task 
                for task in tasks
            }
            
            # Process completed tasks
            for i, future in enumerate(concurrent.futures.as_completed(future_to_task), 1):
                task = future_to_task[future]
                logger.info(f"[{i}/{len(tasks)}] Processing {task.relative_path}")
                
                try:
                    success, message = future.result()
                    logger.info(message)
                    
                    if success:
                        successful_conversions += 1
                    else:
                        failed_conversions += 1
                        
                except Exception as e:
                    error_msg = f"❌ {task.relative_path}: Unexpected error: {str(e)}"
                    logger.error(error_msg)
                    failed_conversions += 1

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("CONVERSION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total files: {len(tasks)}")
    logger.info(f"Successful: {successful_conversions}")
    logger.info(f"Failed: {failed_conversions}")
    
    if failed_conversions > 0:
        logger.warning(f"Some conversions failed. Check the logs above for details.")
        sys.exit(1)
    else:
        logger.info("🎉 All conversions completed successfully!")


if __name__ == "__main__":
    main()
