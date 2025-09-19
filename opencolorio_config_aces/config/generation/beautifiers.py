# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
Beautifiers
===========

Defines various objects related to pattern beautification.
"""

from __future__ import annotations

from opencolorio_config_aces.utilities import (
    multi_replace,
    slugify,
)

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = [
    "SEPARATOR_COLORSPACE_NAME",
    "SEPARATOR_COLORSPACE_FAMILY",
    "SEPARATOR_BUILTIN_TRANSFORM_NAME",
    "PATTERNS_COLORSPACE_NAME",
    "PATTERNS_LOOK_NAME",
    "PATTERNS_TRANSFORM_FAMILY",
    "PATTERNS_VIEW_TRANSFORM_NAME",
    "PATTERNS_DISPLAY_NAME",
    "PATTERNS_ALIAS",
    "beautify_name",
    "beautify_colorspace_name",
    "beautify_look_name",
    "beautify_transform_family",
    "beautify_view_transform_name",
    "beautify_display_name",
    "beautify_alias",
]

SEPARATOR_COLORSPACE_NAME: str = " - "
"""
*OpenColorIO* config colorspace name separator.

SEPARATOR_COLORSPACE_NAME : unicode
"""

SEPARATOR_COLORSPACE_FAMILY: str = "/"
"""
*OpenColorIO* config colorspace family separator.

SEPARATOR_COLORSPACE_FAMILY : unicode
"""

SEPARATOR_BUILTIN_TRANSFORM_NAME: str = "_to_"
"""
*OpenColorIO* config *BuiltinTransform* name separator.

SEPARATOR_BUILTIN_TRANSFORM_NAME : unicode
"""

PATTERNS_COLORSPACE_NAME: dict[str, str] = {
    "ACES_0_1_1": "ACES 0.1.1",
    "ACES_0_2_2": "ACES 0.2.2",
    "ACES_0_7_1": "ACES 0.7.1",
    "_7nits": "",
    "_15nits": "",
    "_": " ",
    "-raw": "",
    "-": " ",
    "\\b(\\w+)limited\\b": "(\\1 Limited)",
    "\\b(\\d+)nits\\b": "(\\1 nits)",
    "RGBmonitor": "sRGB",
    "\\bP3 D": "P3-D",
    "CIE XYZ D65": "CIE XYZ-D65",
    "Gamma1": "Gamma 1",
    "Gamma2": "Gamma 2",
    "Rec1886": "Rec.1886",
    "Rec709": "Rec.709",
    "Rec2020": "Rec.2020",
    "Rec2100": "Rec.2100",
    "ST2084": "ST-2084",
    "Curve\\b": "- Curve",
    "Scene referred": "- Scene-referred",
    "Texture\\b": "- Texture",
    "\\b(\\w)Log": "\\1-Log",
    "\\b(\\w)Gamut": "\\1-Gamut",
    "Cine\\b": ".Cine",
    "EI800": "(EI800)",
    "Linear Rec.709": "Linear Rec.709 (sRGB)",
    "sRGB Encoded Rec.709": "sRGB Encoded Rec.709 (sRGB)",
    "^LogC3": "ARRI LogC3 (EI800)",
    "^LogC4": "ARRI LogC4",
    "AppleLog BT2020": "Apple Log",
    "Log3G10 RWG": "Log3G10 REDWideGamutRGB",
    "Venice S-Log3": "S-Log3 Venice",
}
"""
*OpenColorIO* colorspace name substitution patterns.

Notes
-----
- The substitutions are evaluated in order.

PATTERNS_COLORSPACE_NAME : dict
"""

PATTERNS_COLORSPACE_NAME.update(
    {
        # Input transforms also use the "family" name and thus need beautifying.
        (
            f"{SEPARATOR_COLORSPACE_FAMILY}Alexa"
            f"{SEPARATOR_COLORSPACE_FAMILY}v\\d+"
            f"{SEPARATOR_COLORSPACE_FAMILY}.*"
        ): "",
        f"{SEPARATOR_COLORSPACE_FAMILY}": (SEPARATOR_COLORSPACE_NAME),
    }
)

PATTERNS_LOOK_NAME: dict[str, str] = {
    "Reference Gamut Compress": "ACES 1.3 Reference Gamut Compression",
}
"""
*OpenColorIO* look name substitution patterns.

Notes
-----
- The substitutions are evaluated in order.

PATTERNS_LOOK_NAME : dict
"""

PATTERNS_TRANSFORM_FAMILY: dict[str, str] = {
    "\\\\": SEPARATOR_COLORSPACE_FAMILY,
    "vendorSupplied[/\\\\]": "",
    "arri": "ARRI",
    "alexa": "Alexa",
    "canon": "Canon",
    "panasonic": "Panasonic",
    "red": "RED",
    "sony": "Sony",
}
"""
*OpenColorIO* transform family substitution patterns.

Notes
-----
- The substitutions are evaluated in order.

PATTERNS_TRANSFORM_FAMILY : dict
"""

PATTERNS_VIEW_TRANSFORM_NAME: dict[str, str] = {
    "7.2nit": "&",
    "15nit": "&",
    "lim": " lim",
    "nit": " nits",
    "sim": " sim on",
    "CINEMA": "Cinema",
    "VIDEO": "Video",
    "REC1886": "Rec.1886",
    "REC709": "Rec.709",
    "REC2020": "Rec.2020",
    "-": " ",
}
"""
*OpenColorIO* view transform name substitution patterns.

PATTERNS_VIEW_TRANSFORM_NAME : dict
"""

PATTERNS_DISPLAY_NAME: dict[str, str] = {
    "G2.6-": "",
    "G2.2": "Gamma 2.2",
    "-BFD": "",
    "DisplayP3": "Display P3",
    "REC.1886": "Rec.1886",
    "REC.709": "Rec.709",
    "REC.2020": "Rec.2020",
    "REC.2100": "Rec.2100",
    "-Rec.": " Rec.",
    "-1000nit": "",
    "P3-HDR": "P3 HDR",
    "- MIRROR NEGS": "",
    # Legacy Substitutions
    "dcdm": "DCDM",
    "p3": "P3",
    "rec1886": "Rec.1886",
    "rec709": "Rec.709",
    "rec2020": "Rec.2020",
    "rec2100": "Rec.2100",
}
"""
*OpenColorIO* display name substitution patterns.

Notes
-----
- The substitutions are evaluated in order.

PATTERNS_DISPLAY_NAME : dict
"""

PATTERNS_ALIAS: dict[str, str] = {
    "Curve": "crv",
    "Display P3": "DisplayP3",
    "Gamma ": "g",
    "Linear": "lin",
    "Scene-referred": "scene",
    "Texture": "tx",
    "-Gamut": "gamut",
    "-Log": "log",
    "P3-D6": "p3d6",
}
"""
*OpenColorIO* alias substitution patterns.

Notes
-----
- The substitutions are evaluated in order.

PATTERNS_ALIAS : dict
"""


def beautify_name(name: str, patterns: dict[str, str]) -> str:
    """
    Beautify given name by applying in succession the given patterns.

    Parameters
    ----------
    name : unicode
        Name to beautify.
    patterns : dict
        Dictionary of regular expression patterns and substitution to apply
        onto the name.

    Returns
    -------
    unicode
        Beautified name.

    Examples
    --------
    >>> beautify_name(
    ...     'Rec709_100nits_dim',
    ...     PATTERNS_COLORSPACE_NAME)
    'Rec.709 (100 nits) dim'
    """

    return multi_replace(name, patterns).strip()


def beautify_colorspace_name(name: str) -> str:
    """
    Beautify given *OpenColorIO* `Colorspace` name by applying in succession
    the relevant patterns.

    Parameters
    ----------
    name : unicode
        *OpenColorIO* `Colorspace` name to beautify.

    Returns
    -------
    unicode
        Beautified *OpenColorIO* `Colorspace` name.

    Examples
    --------
    >>> beautify_colorspace_name('Rec709_100nits_dim')
    'Rec.709 (100 nits) dim'
    """

    return beautify_name(name, PATTERNS_COLORSPACE_NAME)


def beautify_look_name(name: str) -> str:
    """
    Beautify given *OpenColorIO* `Look` name by applying in succession the
    relevant patterns.

    Parameters
    ----------
    name : unicode
        *OpenColorIO* `Look` name to beautify.

    Returns
    -------
    unicode
        Beautified *OpenColorIO* `Look` name.

    Examples
    --------
    >>> beautify_look_name('Reference Gamut Compress')
    'ACES 1.3 Reference Gamut Compression'
    """

    return beautify_name(name, PATTERNS_LOOK_NAME)


def beautify_transform_family(name: str) -> str:
    """
    Beautify given *OpenColorIO* `Colorspace` family by applying in succession
    the relevant patterns.

    Parameters
    ----------
    name : unicode
        *OpenColorIO* `Colorspace` family to beautify.

    Returns
    -------
    unicode
        Beautified *OpenColorIO* `Colorspace` family.

    Examples
    --------
    >>> beautify_transform_family('vendorSupplied/arri/alexa/v3/EI800')
    'ARRI/Alexa/v3/EI800'
    """

    return beautify_name(name, PATTERNS_TRANSFORM_FAMILY)


def beautify_view_transform_name(name: str) -> str:
    """
    Beautify given *OpenColorIO* `ViewTransform` name by applying in
    succession the relevant patterns.

    Parameters
    ----------
    name : unicode
        *OpenColorIO* `ViewTransform` name to beautify.

    Returns
    -------
    unicode
        Beautified *OpenColorIO* `ViewTransform` name.

    Examples
    --------
    >>> beautify_view_transform_name(
    ...     'ACES-OUTPUT - ACES2065-1_to_CIE-XYZ-D65 - SDR-CINEMA_1.0')
    'SDR Cinema'
    """

    basename = name.split(SEPARATOR_COLORSPACE_NAME)[-1].split("_")[0]

    tokens = basename.split("-")
    family, genus = (
        ["-".join(tokens[:2]), "-".join(tokens[2:])]
        if len(tokens) > 2
        else [basename, None]
    )

    family = beautify_name(family, PATTERNS_VIEW_TRANSFORM_NAME)

    genus = (
        beautify_name(genus, PATTERNS_VIEW_TRANSFORM_NAME)
        if genus is not None
        else genus
    )

    return f"{family} ({genus})" if genus is not None else family


def beautify_display_name(name: str) -> str:
    """
    Beautify given *OpenColorIO* display name by applying in succession the
    relevant patterns.

    Parameters
    ----------
    name : unicode
        *OpenColorIO* display name to beautify.

    Returns
    -------
    unicode
        Beautified *OpenColorIO* display name.

    Examples
    --------
    >>> beautify_display_name('DISPLAY - CIE-XYZ-D65_to_sRGB')
    'sRGB'
    >>> beautify_display_name('rec709')
    'Rec.709'
    """

    basename = name.split(SEPARATOR_BUILTIN_TRANSFORM_NAME)[-1]

    name = beautify_name(basename, PATTERNS_DISPLAY_NAME)

    return name


def beautify_alias(name: str) -> str:
    """
    Beautify given *OpenColorIO* alias by applying in succession the relevant
    patterns.

    Parameters
    ----------
    name : unicode
        *OpenColorIO* alias to beautify.

    Returns
    -------
    unicode
        Beautified *OpenColorIO* alias.

    Examples
    --------
    >>> beautify_alias('Rec.1886 / Rec.709 Video - Display')
    'rec1886_rec709_video_display'
    >>> beautify_alias('Rec.2100-PQ - Display')
    'rec2100_pq_display'
    >>> beautify_alias('V-Log - Curve')
    'vlog_crv'
    >>> beautify_alias('Gamma 1.8 Rec.709 - Texture')
    'g18_rec709_tx'
    """

    name = beautify_name(name, PATTERNS_ALIAS)

    return slugify(name).replace("-", "_")
