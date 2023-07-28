# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
OpenColorIO Config Generation Common Objects
============================================

Defines various objects related to *OpenColorIO* config generation:

-   :class:`opencolorio_config_aces.ConfigData`
-   :class:`opencolorio_config_aces.serialize_config_data`
-   :class:`opencolorio_config_aces.deserialize_config_data`
-   :func:`opencolorio_config_aces.validate_config`
-   :func:`opencolorio_config_aces.generate_config`
"""

import logging
import PyOpenColorIO as ocio
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from typing import Union

from opencolorio_config_aces.utilities import required
from opencolorio_config_aces.config.generation import (
    PROFILE_VERSION_DEFAULT,
    ProfileVersion,
    colorspace_factory,
    look_factory,
    named_transform_factory,
    view_transform_factory,
)

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = [
    "ConfigData",
    "deserialize_config_data",
    "serialize_config_data",
    "validate_config",
    "generate_config",
]

logger = logging.getLogger(__name__)


@dataclass
class ConfigData:
    """
    Define the data container for an *OpenColorIO* config.

    Parameters
    ----------
    profile_version : ProfileVersion, optional
        Config major and minor version, i.e. (1, 0) or (2, 0).
    name : unicode, optional
        Config name.
    description : unicode, optional
        Config description.
    search_path : list, optional
        Config search path.
    roles : dict
        Config roles, a dict of role and `Colorspace` name.
    colorspaces : array_like
        Config colorspaces, an iterable of
        :attr:`PyOpenColorIO.ColorSpace` class instances or mappings to create
        them with :func:`opencolorio_config_aces.colorspace_factory`
        definition.
    named_transforms : array_like
        Config `NamedTransform`s, an iterable of
        :attr:`PyOpenColorIO.NamedTransfom` class instances or mappings to
        create them with
        :func:`opencolorio_config_aces.named_transform_factory` definition.
    view_transforms : array_like, optional
        Config view transforms, an iterable of
        :attr:`PyOpenColorIO.ViewTransform` class instances or mappings to
        create them with :func:`opencolorio_config_aces.view_transform_factory`
        definition.
    looks : array_like, optional
        Config looks, an iterable of :attr:`PyOpenColorIO.Look` class
        instances or mappings to create them with
        :func:`opencolorio_config_aces.look_factory` definition.
    shared_views : array_like, optional
        Config shared views, an iterable of dicts of view, `ViewTransform`,
        `Colorspace` and rule names, iterable of looks and description.
    views : array_like, optional
        Config views, an iterable of dicts of display, view
        and `Colorspace` names.
    active_displays : array_like, optional
        Config active displays, an iterable of display names.
    active_views : array_like, optional
        Config active displays, an iterable of view names.
    file_rules : array_like, optional
        Config file rules, a dict of file rules.
    viewing_rules : array_like, optional
        Config viewing rules, a dict of viewing rules.
    inactive_colorspaces : array_like, optional
        Config inactive colorspaces, an iterable of `Colorspace` names.
    default_view_transform : unicode, optional
        Name of the default view transform.

    Attributes
    ----------
    schema_version
    profile_version
    name
    description
    search_path
    roles
    colorspaces
    named_transforms
    view_transforms
    looks
    shared_views
    views
    active_displays
    active_views
    file_rules
    viewing_rules
    inactive_colorspaces
    default_view_transform
    """

    schema_version: ProfileVersion = field(
        default_factory=lambda: ProfileVersion(1, 0)
    )
    profile_version: ProfileVersion = field(
        default_factory=lambda: PROFILE_VERSION_DEFAULT
    )
    name: str = field(default_factory=str)
    description: str = (
        'An "OpenColorIO" config generated by "OpenColorIO-Config-ACES".'
    )
    search_path: Union[list] = field(default_factory=list)
    roles: Union[dict] = field(default_factory=dict)
    colorspaces: Union[list] = field(default_factory=list)
    named_transforms: Union[list] = field(default_factory=list)
    view_transforms: Union[list] = field(default_factory=list)
    looks: Union[list] = field(default_factory=list)
    shared_views: Union[list] = field(default_factory=list)
    views: Union[list] = field(default_factory=list)
    active_displays: Union[list] = field(default_factory=list)
    active_views: Union[list] = field(default_factory=list)
    file_rules: Union[list] = field(default_factory=list)
    viewing_rules: Union[list] = field(default_factory=list)
    inactive_colorspaces: Union[list] = field(default_factory=list)
    default_view_transform: str = field(default_factory=str)


@required("jsonpickle")
def deserialize_config_data(path):
    """
    Deserialize the *JSON* *OpenColorIO* config data container at given path.

    Parameters
    ----------
    path : unicode
        *JSON* file path.

    Returns
    -------
    ConfigData
        Deserialized *JSON* *OpenColorIO* config data container.
    """

    import jsonpickle

    with open(path) as config_json:
        return ConfigData(
            **jsonpickle.decode(config_json.read())  # noqa: S301
        )


# TODO: Implement schema verification support for serialized data.
@required("jsonpickle")
def serialize_config_data(data, path):
    """
    Serialize the *OpenColorIO* config data container as a *JSON* file.

    Parameters
    ----------
    data : ConfigData
        *OpenColorIO* config data container to serialize.
    path : unicode
        *JSON* file path.
    """

    import jsonpickle

    with open(path, "w") as config_json:
        config_json.write(jsonpickle.encode(asdict(data), indent=2))


def validate_config(config):
    """
    Validate given *OpenColorIO* config.

    Parameters
    ----------
    config : Config
        *OpenColorIO* config to validate.

    Returns
    -------
    bool
        Whether the *OpenColorIO* config is valid.
    """

    try:
        config.validate()
        return True
    except Exception as error:
        logger.critical(error)
        return False


def generate_config(data, config_name=None, validate=True, base_config=None):
    """
    Generate the *OpenColorIO* config from given data.

    Parameters
    ----------
    data : ConfigData
        *OpenColorIO* config data.
    config_name : unicode, optional
        *OpenColorIO* config file name, if given the config will be written to
        disk.
    validate : bool, optional
        Whether to validate the config.
    base_config : bool, optional
        *OpenColorIO* base config inherited for initial data.

    Returns
    -------
    Config
        *OpenColorIO* config.
    """

    logger.debug("Config data:\n%s", data)

    if base_config is not None:
        config = base_config
    else:
        config = ocio.Config()
        config.setVersion(
            data.profile_version.major, data.profile_version.minor
        )

    if data.name is not None:
        config.setName(data.name)

    if data.description is not None:
        config.setDescription(data.description)

    for search_path in data.search_path:
        logger.debug('Adding "%s".', search_path)
        config.addSearchPath(search_path)

    for role, colorspace in data.roles.items():
        logger.debug('Adding "%s" colorspace as "%s" role.', colorspace, role)
        config.setRole(role, colorspace)

    for colorspace in data.colorspaces:
        if isinstance(colorspace, Mapping):
            colorspace = colorspace_factory(**colorspace)

        logger.debug('Adding "%s" colorspace.', colorspace.getName())
        config.addColorSpace(colorspace)

    for named_transform in data.named_transforms:
        if isinstance(named_transform, Mapping):
            named_transform = named_transform_factory(**named_transform)

        logger.debug('Adding "%s" named transform.', named_transform.getName())
        config.addNamedTransform(named_transform)

    for view_transform in data.view_transforms:
        if isinstance(view_transform, Mapping):
            view_transform = view_transform_factory(**view_transform)

        logger.debug('Adding "%s" view transform.', view_transform.getName())
        config.addViewTransform(view_transform)

    for look in data.looks:
        if isinstance(look, Mapping):
            look = look_factory(**look)

        logger.debug('Adding "%s" look.', look.getName())
        config.addLook(look)

    if data.profile_version.major >= 2:
        logger.debug('Disabling "%s" colorspaces.', data.inactive_colorspaces)
        config.setInactiveColorSpaces(",".join(data.inactive_colorspaces))

    for shared_view in data.shared_views:
        display_colorspace = shared_view.get(
            "display_colorspace", "<USE_DISPLAY_NAME>"
        )
        looks = shared_view.get("looks")
        view_transform = shared_view.get("view_transform")
        rule = shared_view.get("rule")
        description = shared_view.get("description")
        view = shared_view["view"]
        logger.debug(
            'Adding "%s" shared view using "%s" view transform, "%s" display '
            'colorspace, "%s" looks, "%s" rule and "%s" description.',
            view,
            view_transform,
            display_colorspace,
            looks,
            rule,
            description,
        )

        config.addSharedView(
            view, view_transform, display_colorspace, looks, rule, description
        )

    for view in data.views:
        display = view["display"]
        colorspace = view.get("colorspace")
        looks = view.get("looks")
        view_transform = view.get("view_transform")
        display_colorspace = view.get("display_colorspace")
        rule = view.get("rule")
        description = view.get("description")
        view = view["view"]
        if colorspace is not None:
            logger.debug(
                'Adding "%s" view to "%s" display using "%s" colorspace.',
                view,
                display,
                colorspace,
            )

            config.addDisplayView(display, view, colorspace, looks)
        elif view_transform is not None and display_colorspace is not None:
            logger.debug(
                'Adding "%s" view to "%s" display using "%s" view transform, '
                '"%s" display colorspace, "%s" rule and "%s" description.',
                view,
                display,
                view_transform,
                display_colorspace,
                rule,
                description,
            )

            config.addDisplayView(
                display,
                view,
                view_transform,
                display_colorspace,
                looks,
                rule,
                description,
            )
        else:
            logger.debug('Adding "%s" view to "%s" display.', view, display)
            config.addDisplaySharedView(display, view)

    if data.active_displays:
        logger.debug('Activating "%s" displays.', data.active_displays)
        config.setActiveDisplays(",".join(data.active_displays))

    if data.active_views:
        logger.debug('Activating "%s" views.', data.active_views)
        config.setActiveViews(",".join(data.active_views))

    if data.file_rules:
        file_rules = ocio.FileRules()
        rule_index = 0
        for file_rule in reversed(data.file_rules):
            name = file_rule["name"]
            colorspace = file_rule["colorspace"]
            regex = file_rule.get("regex")
            pattern = file_rule.get("pattern")
            extension = file_rule.get("extension")
            if name == "Default":
                logger.debug(
                    'Setting "%s" file rule with "%s" colorspace.',
                    name,
                    colorspace,
                )
                file_rules.setDefaultRuleColorSpace(colorspace)
            elif regex:
                logger.debug(
                    'Adding "%s" file rule with "%s" regex pattern for "%s" '
                    "colorspace.",
                    name,
                    regex,
                    colorspace,
                )
                file_rules.insertRule(rule_index, name, colorspace, regex)
                rule_index += 1
            else:
                logger.debug(
                    'Adding "%s" file rule with "%s" pattern and "%s" '
                    'extension for "%s" colorspace.',
                    name,
                    pattern,
                    extension,
                    colorspace,
                )
                file_rules.insertRule(
                    rule_index, name, colorspace, pattern, extension
                )
                rule_index += 1
        config.setFileRules(file_rules)

    if data.viewing_rules:
        viewing_rules = ocio.ViewingRules()
        for _i, _viewing_rule in enumerate(reversed(data.viewing_rules)):
            logger.warning("Inserting a viewing rule is not supported yet!")
            # viewing_rules.insertRule()
        config.setViewingRules(viewing_rules)

    if data.default_view_transform is not None:
        config.setDefaultViewTransformName(data.default_view_transform)

    if validate:
        validate_config(config)

    if config_name is not None:
        with open(config_name, "w") as file:
            file.write(config.serialize())

    return config


if __name__ == "__main__":
    from opencolorio_config_aces.utilities import ROOT_BUILD_DEFAULT

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    build_directory = (
        ROOT_BUILD_DEFAULT / "config" / "common" / "tests"
    ).resolve()

    logger.info('Using "%s" build directory...', build_directory)

    build_directory.mkdir(parents=True, exist_ok=True)

    # "OpenColorIO 1" configuration.
    colorspace_1 = {"name": "Gamut - sRGB", "family": "Gamut"}
    colorspace_2 = {
        "name": "CCTF - sRGB",
        "family": "CCTF",
        "description": (
            'WARNING: The sRGB "EOTF" is purposely incorrect and '
            "only a placeholder!"
        ),
        "to_reference": {
            "transform_type": "ExponentTransform",
            "value": [2.2, 2.2, 2.2, 1],
        },
    }
    colorspace_3 = {
        "name": "Colorspace - sRGB",
        "family": "Colorspace",
        "to_reference": {
            "transform_type": "ColorSpaceTransform",
            "src": "CCTF - sRGB",
            "dst": "Gamut - sRGB",
        },
    }
    colorspace_4 = colorspace_factory(
        **{"name": "Utility - Raw", "family": "Utility", "is_data": True}
    )

    _red_cdl_transform = ocio.CDLTransform()
    _red_cdl_transform.setSlope([0, 0, 0])
    _red_cdl_transform.setOffset([1, 0, 0])
    look_1 = look_factory("Look - Red", forward_transform=_red_cdl_transform)
    look_2 = {
        "name": "Look - Green",
        "forward_transform": {
            "transform_type": "CDLTransform",
            "slope": [0, 0, 0],
            "offset": [0, 1, 0],
        },
    }
    _gain_cdl_transform = ocio.CDLTransform()
    _gain_cdl_transform.setSlope([0.5, 0.5, 0.5])
    look_3 = {
        "name": "Look - Quarter Blue",
        "forward_transform": [  # Note the nested "GroupTransform"s.
            [
                {
                    "transform_type": "CDLTransform",
                    "slope": [0, 0, 0],
                    "offset": [0, 1, 0],
                },
                _gain_cdl_transform,
            ],
            _gain_cdl_transform,
        ],
    }
    display_1 = {
        "name": "View - sRGB Monitor - sRGB",
        "family": "View",
        "base_colorspace": colorspace_3,
    }

    data = ConfigData(
        roles={ocio.ROLE_SCENE_LINEAR: "Gamut - sRGB"},
        colorspaces=[
            colorspace_1,
            colorspace_2,
            colorspace_3,
            colorspace_4,
            display_1,
        ],
        looks=[look_1, look_2, look_3],
        views=[
            {
                "display": "sRGB Monitor",
                "view": "sRGB - sRGB",
                "colorspace": display_1["name"],
            },
            {
                "display": "sRGB Monitor",
                "view": "Raw",
                "colorspace": colorspace_4.getName(),
            },
        ],
        active_displays=["sRGB Monitor"],
        active_views=["sRGB - sRGB"],
    )

    generate_config(data, build_directory / "config-v1.ocio")

    # TODO: Pickling "PyOpenColorIO.ColorSpace" fails on early "PyOpenColorIO"
    # versions.
    try:
        serialize_config_data(data, build_directory / "config-v1.json")
    except TypeError as error:
        logger.critical(error)

    # "OpenColorIO 2" configuration.
    colorspace_1 = {
        "name": "ACES - ACES2065-1",
        "family": "ACES",
        "aliases": "lin_ap0",
    }
    colorspace_2 = {
        "name": "ACES - ACEScg",
        "family": "ACES",
        "to_reference": {
            "transform_type": "BuiltinTransform",
            "style": "ACEScg_to_ACES2065-1",
        },
        "aliases": ["lin_ap1"],
    }
    colorspace_3 = {
        "name": "Gamut - sRGB",
        "family": "Gamut",
        "to_reference": {
            "transform_type": "MatrixTransform",
            "matrix": [
                0.4387956642,
                0.3825367756,
                0.1787151431,
                0.0000000000,
                0.0890560064,
                0.8126211313,
                0.0982957371,
                0.0000000000,
                0.0173063724,
                0.1083658908,
                0.8742745984,
                0.0000000000,
                0.0000000000,
                0.0000000000,
                0.0000000000,
                1.0000000000,
            ],
        },
    }
    colorspace_4 = {
        "name": "CCTF - sRGB",
        "family": "CCTF",
        "to_reference": {
            "transform_type": "ExponentWithLinearTransform",
            "gamma": [2.4, 2.4, 2.4, 1],
            "offset": [0.055, 0.055, 0.055, 0],
        },
    }
    colorspace_5 = {
        "name": "Utility - Raw",
        "family": "Utility",
        "is_data": True,
    }

    named_transform_1 = {
        "name": "+1 Stop",
        "family": "Exposure",
        "forward_transform": {
            "transform_type": "MatrixTransform",
            "matrix": [
                2.0000000000,
                0.0000000000,
                0.0000000000,
                0.0000000000,
                0.0000000000,
                2.0000000000,
                0.0000000000,
                0.0000000000,
                0.0000000000,
                0.0000000000,
                2.0000000000,
                0.0000000000,
                0.0000000000,
                0.0000000000,
                0.0000000000,
                1.0000000000,
            ],
        },
    }
    look_1 = {
        "name": "Look - Red",
        "forward_transform": {
            "transform_type": "CDLTransform",
            "slope": [0, 0, 0],
            "offset": [1, 0, 0],
        },
    }

    interchange = {"name": "CIE-XYZ D65"}

    display_1 = {
        "name": "sRGB Monitor",
        "from_reference": {
            "transform_type": "BuiltinTransform",
            "style": "DISPLAY - CIE-XYZ-D65_to_sRGB",
        },
        "reference_space": "REFERENCE_SPACE_DISPLAY",
    }
    display_2 = {
        "name": "ITU-R BT.1886 Monitor",
        "from_reference": {
            "transform_type": "BuiltinTransform",
            "style": "DISPLAY - CIE-XYZ-D65_to_REC.1886-REC.709",
        },
        "reference_space": "REFERENCE_SPACE_DISPLAY",
    }

    view_transform_1 = {
        "name": "ACES Output - SDR Video - 1.0",
        "from_reference": {
            "transform_type": "BuiltinTransform",
            "style": "ACES-OUTPUT - ACES2065-1_to_CIE-XYZ-D65 - SDR-VIDEO_1.0",
        },
    }
    view_transform_2 = {
        "name": "Output - No Tonescale",
        "from_reference": {
            "transform_type": "BuiltinTransform",
            "style": "UTILITY - ACES-AP0_to_CIE-XYZ-D65_BFD",
        },
    }

    displays = (display_1, display_2)
    view_transforms = (view_transform_1, view_transform_2)
    shared_views = [
        {
            "display": display["name"],
            "view": view_transform["name"],
            "view_transform": view_transform["name"],
        }
        for display in displays
        for view_transform in view_transforms
    ]

    data = ConfigData(
        profile_version=PROFILE_VERSION_DEFAULT,
        roles={
            "aces_interchange": "ACES - ACES2065-1",
            "cie_xyz_d65_interchange": "CIE-XYZ D65",
            ocio.ROLE_DEFAULT: "ACES - ACES2065-1",
            ocio.ROLE_SCENE_LINEAR: colorspace_2["name"],
        },
        colorspaces=[
            colorspace_1,
            colorspace_2,
            colorspace_3,
            colorspace_4,
            colorspace_5,
            interchange,
            display_1,
            display_2,
        ],
        named_transforms=[named_transform_1],
        looks=[look_1],
        view_transforms=[view_transform_1, view_transform_2],
        inactive_colorspaces=["CIE-XYZ D65"],
        shared_views=shared_views,
        views=shared_views
        + [
            {
                "display": display["name"],
                "view": "Raw",
                "colorspace": "Utility - Raw",
            }
            for display in displays
        ],
        active_displays=[display_1["name"], display_2["name"]],
        active_views=[
            view_transform["name"] for view_transform in view_transforms
        ]
        + ["Raw"],
        file_rules=[
            {
                "name": "Linear - sRGB",
                "colorspace": "Gamut - sRGB",
                "regex": "_[sS][rR][gG][bB]\\.([eE][xX][rR]|[hH][dD][rR])$",
            },
            {
                "name": "EOTF - sRGB",
                "colorspace": "CCTF - sRGB",
                "regex": "_[sS][rR][gG][bB]\\.([pP][nN][gG]|[tT][iI][fF])$",
            },
            {"name": "Default", "colorspace": "ACES - ACES2065-1"},
        ],
        viewing_rules=[],
    )

    config = generate_config(data, build_directory / "config-v2.ocio")

    # TODO: Pickling "PyOpenColorIO.ColorSpace" fails on early "PyOpenColorIO"
    # versions.
    try:
        serialize_config_data(data, build_directory / "config-v2.json")
    except TypeError as error:
        logger.critical(error)

    named_transform_2 = {
        "name": "-1 Stop",
        "family": "Exposure",
        "forward_transform": {
            "transform_type": "MatrixTransform",
            "matrix": [
                -2.0000000000,
                0.0000000000,
                0.0000000000,
                0.0000000000,
                0.0000000000,
                -2.0000000000,
                0.0000000000,
                0.0000000000,
                0.0000000000,
                0.0000000000,
                -2.0000000000,
                0.0000000000,
                0.0000000000,
                0.0000000000,
                0.0000000000,
                1.0000000000,
            ],
        },
    }

    data = ConfigData(named_transforms=[named_transform_2])

    generate_config(
        data,
        build_directory / "config-v2-with-named-transform.ocio",
        base_config=config,
    )

    # TODO: Pickling "PyOpenColorIO.ColorSpace" fails on early "PyOpenColorIO"
    # versions.
    try:
        serialize_config_data(
            data, build_directory / "config-v2-with-named-transform.json"
        )
    except TypeError as error:
        logger.critical(error)
