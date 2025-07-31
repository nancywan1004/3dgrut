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

from hydra.compose import compose
from hydra.initialize import initialize
from omegaconf import DictConfig

from threedgrut.export.usdz_exporter import USDZExporter
from threedgrut.model.model import MixtureOfGaussians

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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


def main():
    parser = argparse.ArgumentParser(description="Convert PLY to USDZ")
    parser.add_argument("input_file", type=str, help="Input PLY file path")
    parser.add_argument("--output_file", type=str,
                        help="Output USDZ file path (defaults to input file path with .usdz extension)")
    parser.add_argument("--force_zero_order_sh", action="store_true", default=True,
                        help="Force conversion to 0-order spherical harmonics for Isaac Sim 5.0 compatibility (default: True)")

    args = parser.parse_args()

    input_path = Path(args.input_file)

    # Validate input file
    if not input_path.exists():
        logger.error(f"Input file does not exist: {input_path}")
        sys.exit(1)

    if input_path.suffix.lower() != ".ply":
        logger.error(f"Input file must be a PLY file: {input_path}")
        sys.exit(1)

    # Determine output path
    if args.output_file:
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_path = input_path.with_suffix(".usdz")

    logger.info(f"Converting {input_path} to {output_path}")
    if args.force_zero_order_sh:
        logger.info("Forcing 0-order spherical harmonics for Isaac Sim 5.0 compatibility")

    try:
        # 1. Create model with default config
        logger.info("Loading default configuration")
        conf = load_default_config()

        # Override spherical harmonics degree to 0 for Isaac Sim compatibility
        if args.force_zero_order_sh:
            conf.model.progressive_training.max_n_features = 0
            conf.model.progressive_training.init_n_features = 0
            # Also update the render configuration to match
            conf.render.particle_radiance_sph_degree = 0
            logger.info("Set max_n_features and init_n_features to 0 for 0-order SH")
            logger.info("Set particle_radiance_sph_degree to 0 for consistent rendering")

        model = MixtureOfGaussians(conf)

        # 2. Use init_from_ply with modified loading for 0-order SH
        logger.info(f"Loading PLY with init_from_ply: {input_path}")
        if args.force_zero_order_sh:
            model.init_from_ply_zero_order_sh(str(input_path), init_model=False)
        else:
            model.init_from_ply(str(input_path), init_model=False)

        # 3. Create USDZExporter
        exporter = USDZExporter()

        # 4. Export to USDZ
        logger.info(f"Exporting with USDZExporter: {output_path}")
        exporter.export(model, output_path, dataset=None, conf=conf)

        logger.info(f"Successfully exported to {output_path}")
    except Exception as e:
        logger.error(f"Error processing PLY file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
