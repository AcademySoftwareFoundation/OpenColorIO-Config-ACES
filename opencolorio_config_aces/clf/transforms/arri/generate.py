# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*ARRI* CLF Transforms Generation
=======================================

Defines procedures for generating ARRI *Common LUT Format* (CLF)
transforms for the OpenColorIO project.
"""


from math import log, log10
import PyOpenColorIO as ocio
from pathlib import Path
import sys


__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = [
    "generate_logc3",
    "generate_logc4",
]

THIS_DIR = Path(__file__).parent.resolve()

TF_ID_PREFIX = "urn:aswf:ocio:transformId:1.0:"
TF_ID_SUFFIX = ":1.0"

CLF_SUFFIX = ".clf"


def generate_logc3(ei=800, clipping=True, debug=False):
    """Generate ARRI LogC3 CLF transforms.

    This method provides the connecting derivation between the public aces-dev IDT
    "v3_IDT_maker" code and the "ALEXA Log C Curve Usage in VFX 09-Mar-17" White Paper
    parameters, which also conform to the required CLF cameraLogToLin parameters.

    Currently only EI values between 160 and 1280 are supported.

    Parameters
    ----------
    ei : int
        EI value to generate, must be 160 <= EI < 1280.

    clipping : bool
        Clip input domain to [0.0, 1.0] to match IDT 1D LUT behavior. Required
        for a precise match to 'ctlrender' processing.

    debug : bool
        Whether to print additional information for diagnostics.

    Returns
    -------
    bool
    """

    if not (160 <= ei <= 1280):
        print(
            f"Error: Unsupported EI{ei:d} requested, must be 160 <= EI < 1280".format(
                ei
            )
        )
        return False

    # v3_IDT_maker.py parameters
    nominalEI = 400
    midGraySignal = 0.01
    encodingGain = 500 / 1023 * 0.525  # was: 0.256598
    encodingOffset = 400 / 1023  # was: 0.391007
    cutPoint = 1 / 9  # renamed from "cut"
    slope = 1 / (cutPoint * log(10))
    offset = log10(cutPoint) - slope * cutPoint
    gain = ei / nominalEI
    gray = midGraySignal / gain
    encGain = (log(gain) / log(2) * (0.89 - 1) / 3 + 1) * encodingGain
    encOffset = encodingOffset

    for i in range(0, 3):
        nz = ((95 / 1023 - encOffset) / encGain - offset) / slope
        encOffset = encodingOffset - log10(1 + nz) * encGain

    # derived "ALEXA Log C Curve Usage in VFX 09-Mar-17" style parameters
    # compatible with CLF cameraLogToLin parameters
    cut = (cutPoint - nz) * gray * (0.18 / (midGraySignal * nominalEI / ei))
    a = 1.0 / (gray * 0.18 / (midGraySignal * nominalEI / ei))
    b = nz
    c = encGain
    d = encOffset

    if debug:

        # unused variables for completeness
        e = c * (
            a / ((a * cut + b) * log(10))
        )  # follows CLF 6.6 Log specification
        f = (
            c * log10(a * cut + b) + d
        ) - e * cut  # follows CLF 6.6 Log specification

        print(f"White Paper Values for EI{ei:d}")
        print(f"cut: {cut:.6f} :: {cut:.15f}")
        print(f"a:   {a:.6f} :: {a:.15f}")
        print(f"b:   {b:.6f} :: {b:.15f}")
        print(f"c:   {c:.6f} :: {c:.15f}")
        print(f"d:   {d:.6f} :: {d:.15f}")
        print(f"e:   {e:.6f} :: {e:.15f}")
        print(f"f:   {f:.6f} :: {f:.15f}")

    config = ocio.Config.CreateRaw()

    lct = ocio.LogCameraTransform(
        base=10,
        linSideBreak=[cut, cut, cut],
        logSideSlope=[c, c, c],
        logSideOffset=[d, d, d],
        linSideSlope=[a, a, a],
        linSideOffset=[b, b, b],
        direction=ocio.TRANSFORM_DIR_INVERSE,
    )

    # consistent with ARRI aces-dev IDT
    mtx = [
        [6.8020600000000e-01, 2.3613700000000e-01, 8.3658000000000e-02],
        [8.5415000000000e-02, 1.0174710000000e00, -1.0288600000000e-01],
        [2.0570000000000e-03, -6.2563000000000e-02, 1.0605060000000e00],
    ]

    if clipping:
        # Range Transform to mimic clipping behavior of IDT 1D LUT
        rt = ocio.RangeTransform()
        rt.setMinInValue(0.0)
        rt.setMaxInValue(1.0)
        rt.setMinOutValue(0.0)
        rt.setMaxOutValue(1.0)
        rt.setStyle(ocio.RangeStyle.RANGE_CLAMP)

        transform_list = [rt, lct, package_matrix(mtx)]

    else:
        transform_list = [lct, package_matrix(mtx)]

    gt = ocio.GroupTransform(transform_list)

    aces_id = f"urn:ampas:aces:transformId:v1.5:IDT.ARRI.Alexa-v3-logC-EI{ei:d}.a1.v2"

    # Write file compliant with new naming convention
    clf_id = (
        TF_ID_PREFIX
        + f"ARRI:Input:ARRI_LogC3_EI{ei:d}_to_ACES2065-1".format(ei)
        + TF_ID_SUFFIX
    )

    fmdg = gt.getFormatMetadata()
    fmdg.setID(clf_id)
    fmdg.addChildElement(
        "Description", f"ARRI LogC3 (EI{ei:d}) to ACES2065-1".format(ei)
    )
    fmdg.addChildElement(
        "InputDescriptor", f"ARRI LogC3 (EI{ei:d})".format(ei)
    )
    fmdg.addChildElement("OutputDescriptor", "ACES2065-1")
    fmdg.addChildElement("Info", "")
    info = fmdg.getChildElements()[3]
    info.addChildElement("ACEStransformID", aces_id)

    dest_dir = THIS_DIR / "input"
    if not dest_dir.exists():
        dest_dir.mkdir()

    fname = dest_dir / (
        f"ARRI.LogC3_EI{ei:d}_to_ACES2065-1".format(ei) + CLF_SUFFIX
    )
    gt.write("Academy/ASC Common LUT Format", str(fname), config)

    return True


def generate_logc4(debug=False):
    """Generate ARRI LogC4 CLF transforms.

    Parameters
    ----------
    debug : bool
        Whether to print additional information for diagnostics.

    Returns
    -------
    bool
    """

    config = ocio.Config.CreateRaw()

    # Parameters as defined in
    # "ARRI LogC4 Logarithmic Color Space Specification - 1st May 2022"
    # Parameters as defined in aces-dev CTL
    a = (2.0**18.0 - 16.0) / 117.45
    b = (1023.0 - 95.0) / 1023.0
    c = 95.0 / 1023.0
    s = (7.0 * log(2.0) * pow(2.0, 7.0 - 14.0 * c / b)) / (a * b)
    t = (pow(2.0, 14.0 * (-c / b) + 6.0) - 64.0) / a

    # Derived parameters compliant with CLF cameraLogToLin
    LIN_SIDE_SLP = a
    LIN_SIDE_OFF = 64.0
    LOG_SIDE_SLP = b / 14.0
    LOG_SIDE_OFF = -6.0 * b / 14.0 + c
    LIN_SIDE_BRK = t
    BASE = 2.0

    # Verify that the default linear slope and offset that will be calculated by OCIO
    # are sufficiently close to the constants used in the reference CTL.
    if debug:
        LINEAR_SLOPE = (
            LOG_SIDE_SLP
            * LIN_SIDE_SLP
            / ((LIN_SIDE_SLP * LIN_SIDE_BRK + LIN_SIDE_OFF) * log(BASE))
        )
        LOG_SB = LOG_SIDE_OFF + LOG_SIDE_SLP * log(
            LIN_SIDE_SLP * LIN_SIDE_BRK + LIN_SIDE_OFF
        ) / log(BASE)
        LINEAR_OFFSET = LOG_SB - LINEAR_SLOPE * LIN_SIDE_BRK
        print(LINEAR_SLOPE, LINEAR_OFFSET, 1.0 / s, -t / s)
    # This prints:
    #  8.803033210331753 0.15895633652241092 8.803033210331753 0.15895633652241087
    # indicating the default values have sufficient accuracy.

    lct = ocio.LogCameraTransform(
        base=BASE,
        linSideBreak=[LIN_SIDE_BRK, LIN_SIDE_BRK, LIN_SIDE_BRK],
        logSideSlope=[LOG_SIDE_SLP, LOG_SIDE_SLP, LOG_SIDE_SLP],
        logSideOffset=[LOG_SIDE_OFF, LOG_SIDE_OFF, LOG_SIDE_OFF],
        linSideSlope=[LIN_SIDE_SLP, LIN_SIDE_SLP, LIN_SIDE_SLP],
        linSideOffset=[LIN_SIDE_OFF, LIN_SIDE_OFF, LIN_SIDE_OFF],
        direction=ocio.TRANSFORM_DIR_INVERSE,
    )

    # Values as defined in:
    # "ARRI LogC4 Logarithmic Color Space Specification - 1st May 2022"
    mtx = [
        [0.7509573628, 0.1444227867, 0.1046198505],
        [0.0008218371, 1.0073975849, -0.0082194220],
        [-0.0004999521, -0.0008541772, 1.0013541294],
    ]

    gt = ocio.GroupTransform([lct, package_matrix(mtx)])

    clf_id = (
        TF_ID_PREFIX + "ARRI:Input:ARRI_LogC4_to_ACES2065-1" + TF_ID_SUFFIX
    )

    # Consistent with CTL in aces-dev PR:
    aces_id = "urn:ampas:aces:transformId:v1.5:IDT.ARRI.LogC4.a1.v1"

    fmdg = gt.getFormatMetadata()
    fmdg.setID(clf_id)
    fmdg.addChildElement("Description", "ARRI LogC4 to ACES2065-1")
    fmdg.addChildElement("InputDescriptor", "ARRI LogC4")
    fmdg.addChildElement("OutputDescriptor", "ACES2065-1")
    fmdg.addChildElement("Info", "")
    info = fmdg.getChildElements()[3]
    info.addChildElement("ACEStransformID", aces_id)

    dest_dir = THIS_DIR / "input"
    if not dest_dir.exists():
        dest_dir.mkdir()

    fname = dest_dir / ("ARRI.LogC4_to_ACES2065-1" + CLF_SUFFIX)
    gt.write("Academy/ASC Common LUT Format", str(fname), config)

    return True


def package_matrix(mtx):
    """Package a 3x3 matrix as an OCIO Matrix transform."""

    coefs4x4 = [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
    ]
    coefs4x4[0:3] = mtx[0]
    coefs4x4[4:7] = mtx[1]
    coefs4x4[8:11] = mtx[2]
    offs = [0.0, 0.0, 0.0, 0.0]
    direc = ocio.TRANSFORM_DIR_FORWARD
    mtxOp = ocio.MatrixTransform(coefs4x4, offs, direc)
    return mtxOp


def main():
    generate_logc3(800, False)
    generate_logc4()
    return 0


if __name__ == "__main__":
    sys.exit(main())
