# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
OpenColorIO Config Generation Spreadsheet
=========================================
"""

from __future__ import annotations

__all__ = [
    "URL_SPREADSHEET_CONFIG_TRANSFORMS",
    "url_export_transforms_mapping_file",
]

URL_SPREADSHEET_CONFIG_TRANSFORMS: str = (
    "https://docs.google.com/spreadsheets/d/"
    "1V6tbYwPOK8fssOpO91LTUMV_5Lj1ULjadz65r4zxBHw"
)
"""URL to the unified *OpenColorIO-Config-ACES* transforms spreadsheet."""


def url_export_transforms_mapping_file(gid: int) -> str:
    """Return the *CSV* export URL for the given mapping sheet identifier."""

    return f"{URL_SPREADSHEET_CONFIG_TRANSFORMS}/export?format=csv&gid={gid}"
