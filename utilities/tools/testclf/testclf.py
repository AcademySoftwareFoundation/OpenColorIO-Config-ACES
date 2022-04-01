# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
Test CLF
========

CLI tool to apply a Common LUT Format (CLF) transform to input RGB data
to test its accuracy.

This module can also be imported and the function ``test_clf`` called
to use the tool programmatically.
"""

import argparse
import sys
import traceback

import numpy as np
import imageio
import PyOpenColorIO as ocio

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = ["test_clf"]


def test_clf(clf_path, input_data, output_path, inverse=False):
    """
    Apply a Common LUT Format (CLF) transform to input RGB data to test
    its accuracy. Recommended image format: OpenEXR.

    Parameters
    ----------
    clf_path : str
        *CLF* transform file path.
    input_data : list[str]
        Single input image file path or one or more "," delimited RGB
        float triplet strings
        (e.g. ["1.0,0.0,0.0", "0.0,0.1,0.0", "0,0,1"]).
    output_path : str, optional
        Output image file path, required when an input image file is
        specified.
    inverse : bool, optional
        Whether to apply transform in the inverse direction.

    Raises
    ------
    RuntimeError
        If the input parameters are invalid.
    """
    output_image = False
    num_channels = 3

    if "," in input_data[0]:
        # Interpret as RGB array
        src_rgb = np.array(
            [list(map(float, c.split(","))) for c in input_data], dtype=np.float32
        )
        if not src_rgb.shape == (len(input_data), 3):
            raise RuntimeError(
                f"Invalid input array shape {src_rgb.shape}. Expected (N, 3)."
            )
    else:
        # Interpret as RGB image path
        src_rgb = imageio.imread(input_data[0])
        num_channels = src_rgb.shape[2]

        output_image = True
        if not output_path:
            raise RuntimeError(
                "Output path (-o OUTPUT, --output OUTPUT) required when input is an "
                "image file."
            )

    # Create default OCIO config
    config = ocio.Config.CreateRaw()

    # Build a processor from a single transform
    file_tf = ocio.FileTransform(
        src=clf_path,
        interpolation=ocio.INTERP_BEST,
        direction=ocio.TRANSFORM_DIR_INVERSE if inverse else ocio.TRANSFORM_DIR_FORWARD,
    )
    proc = config.getProcessor(file_tf)
    cpu_proc = proc.getDefaultCPUProcessor()

    # Apply file transform to a copy of src pixels in-place. Preserve src for
    # comparison.
    dst_rgb = np.copy(src_rgb)

    if num_channels == 4:
        cpu_proc.applyRGBA(dst_rgb)
    elif num_channels == 3:
        cpu_proc.applyRGB(dst_rgb)
    else:
        raise RuntimeError(
            f"Unsupported number of channels ({num_channels}) in input data. Image "
            f"must be RGB (3) or RGBA (4)."
        )

    if output_image:
        # Write array to output image
        imageio.imwrite(output_path, dst_rgb)
    else:
        # Print pixel transformations
        for src_pixel, dst_pixel in zip(src_rgb, dst_rgb):
            print(
                f"{', '.join(map(str, src_pixel))} -> "
                f"{', '.join(map(str, dst_pixel))}"
            )


if __name__ == "__main__":
    # Tool interface
    parser = argparse.ArgumentParser(
        description="Apply a Common LUT Format (CLF) transform to input RGB data to "
        "test its accuracy. Recommended image format: OpenEXR."
    )
    parser.add_argument(
        "clf",
        type=str,
        help="CLF transform file.",
    )
    parser.add_argument(
        "input",
        type=str,
        nargs="+",
        help="Input image file or one or more ',' delimited RGB float triplets "
        "(e.g. 1.0,0.0,0.0 0.0,0.1,0.0 0,0,1).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output image file, required when an input image file is specified.",
    )
    parser.add_argument(
        "-i",
        "--inverse",
        action="store_true",
        help="Apply transform in the inverse direction.",
    )

    # Parse arguments
    args = parser.parse_args()

    # Run tool and exit
    exit_code = 1

    try:
        test_clf(args.clf, args.input, args.output, args.inverse)
        exit_code = 0
    except Exception as e:
        traceback.print_exc()
        print(f"An error occurred: {e}")

    sys.exit(exit_code)
