# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*aces-dev* Analytical Reference Config Generator
================================================

Defines various objects related to the generation of the analytical *aces-dev*
reference *OpenColorIO* config.
"""

import itertools
import logging

import PyOpenColorIO as ocio

from opencolorio_config_aces.config.generation import (
    BUILD_CONFIGURATIONS,
    BUILTIN_TRANSFORMS,
    PROFILE_VERSION_DEFAULT,
    SEPARATOR_BUILTIN_TRANSFORM_NAME,
    SEPARATOR_COLORSPACE_NAME,
    BuildConfiguration,
    ConfigData,
    beautify_display_name,
    beautify_name,
    colorspace_factory,
    generate_config,
)
from opencolorio_config_aces.config.reference import (
    DescriptionStyle,
    build_aces_conversion_graph,
    classify_aces_ctl_transforms,
    conversion_path,
    discover_aces_ctl_transforms,
    filter_ctl_transforms,
    filter_nodes,
    node_to_ctl_transform,
)
from opencolorio_config_aces.config.reference.discover.graph import (
    SEPARATOR_NODE_NAME_CTL,
)
from opencolorio_config_aces.config.reference.generate.config import (
    COLORSPACE_SCENE_ENCODING_REFERENCE,
    ctl_transform_to_colorspace,
)
from opencolorio_config_aces.utilities import required, timestamp

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = [
    "PATTERNS_VIEW_NAME_REFERENCE",
    "beautify_view_name",
    "create_builtin_transform",
    "node_to_builtin_transform",
    "node_to_colorspace",
    "config_basename_aces",
    "config_name_aces",
    "config_description_aces",
    "generate_config_aces",
    "main",
]

LOGGER = logging.getLogger(__name__)

PATTERNS_VIEW_NAME_REFERENCE = {
    "\\(100 nits\\) dim": "",
    "\\(100 nits\\)": "",
    "\\(48 nits\\)": "",
    f"Output{SEPARATOR_COLORSPACE_NAME}": "",
}
"""
*OpenColorIO* view name substitution patterns.

PATTERNS_VIEW_NAME_REFERENCE : dict
"""


def beautify_view_name(name):
    """
    Beautifie given *OpenColorIO* view name by applying in succession the
    relevant patterns.

    Parameters
    ----------
    name : unicode
        *OpenColorIO* view name to beautify.

    Returns
    -------
    unicode
        Beautified *OpenColorIO* view name.

    Examples
    --------
    >>> beautify_view_name('Rec. 709 (100 nits) dim')
    'Rec. 709'
    """

    return beautify_name(name, PATTERNS_VIEW_NAME_REFERENCE)


def create_builtin_transform(style, profile_version=PROFILE_VERSION_DEFAULT):
    """
    Create an *OpenColorIO* builtin transform for given style.

    If the style does not exist, a placeholder transform is used in place
    of the builtin transform.

    Parameters
    ----------
    style : unicode
        *OpenColorIO* builtin transform style.
    profile_version : ProfileVersion, optional
        *OpenColorIO* config profile version.

    Returns
    -------
    BuiltinTransform
        *OpenColorIO* builtin transform for given style.
    """

    try:
        if BUILTIN_TRANSFORMS.get(style, PROFILE_VERSION_DEFAULT) > profile_version:
            raise ValueError()  # noqa: TRY301

        builtin_transform = ocio.BuiltinTransform()
        builtin_transform.setStyle(style)
    except (ValueError, ocio.Exception) as error:
        if isinstance(error, ValueError):
            LOGGER.warning(
                '"%s" style is unavailable for "%s" profile version!',
                style,
                profile_version,
            )
        else:
            LOGGER.warning(
                '"%s" style is either undefined using a placeholder '
                '"FileTransform" instead!',
                style,
            )
        builtin_transform = ocio.FileTransform()
        builtin_transform.setSrc(style)

    return builtin_transform


@required("NetworkX")
def node_to_builtin_transform(
    graph,
    node,
    profile_version=PROFILE_VERSION_DEFAULT,
    direction="Forward",
):
    """
    Generate the *OpenColorIO* builtin transform for given *aces-dev*
    conversion graph node.

    Parameters
    ----------
    graph : DiGraph
        *aces-dev* conversion graph.
    node : unicode
        Node name to generate the *OpenColorIO* builtin transform for.
    profile_version : ProfileVersion, optional
        *OpenColorIO* config profile version.
    direction : unicode, optional
        {'Forward', 'Reverse'},

    Returns
    -------
    BuiltinTransform
        *OpenColorIO* builtin transform.
    """

    from networkx.exception import NetworkXNoPath

    try:
        transform_styles = []

        path = (node, COLORSPACE_SCENE_ENCODING_REFERENCE)
        path = path if direction.lower() == "forward" else reversed(path)
        path = conversion_path(graph, *path)

        if not path:
            return None

        verbose_path = " --> ".join(dict.fromkeys(itertools.chain.from_iterable(path)))
        LOGGER.debug('Creating "BuiltinTransform" with "%s" path.', verbose_path)

        for edge in path:
            source, target = edge
            transform_styles.append(
                f"{source.split(SEPARATOR_NODE_NAME_CTL)[-1]}"
                f"{SEPARATOR_BUILTIN_TRANSFORM_NAME}"
                f"{target.split(SEPARATOR_NODE_NAME_CTL)[-1]}"
            )

        if len(transform_styles) == 1:
            builtin_transform = create_builtin_transform(
                transform_styles[0], profile_version
            )

            return builtin_transform
        else:
            group_transform = ocio.GroupTransform()

            for transform_style in transform_styles:
                builtin_transform = create_builtin_transform(transform_style)
                group_transform.appendTransform(builtin_transform)

            return group_transform

    except NetworkXNoPath:
        LOGGER.debug(
            'No path to "%s" for "%s" node!',
            COLORSPACE_SCENE_ENCODING_REFERENCE,
            node,
        )


def node_to_colorspace(
    graph,
    node,
    profile_version=PROFILE_VERSION_DEFAULT,
    describe=DescriptionStyle.LONG_UNION,
):
    """
    Generate the *OpenColorIO* `Colorspace` for given *aces-dev* conversion
    graph node.

    Parameters
    ----------
    graph : DiGraph
        *aces-dev* conversion graph.
    node : unicode
        Node name to generate the *OpenColorIO* `Colorspace` for.
    profile_version : ProfileVersion, optional
        *OpenColorIO* config profile version.
    describe : int, optional
        Any value from the
        :class:`opencolorio_config_aces.DescriptionStyle` enum.

    Returns
    -------
    ocio.ColorSpace
        *OpenColorIO* colorspace.
    """

    ctl_transform = node_to_ctl_transform(graph, node)

    colorspace = ctl_transform_to_colorspace(
        ctl_transform,
        describe=describe,
        scheme="Legacy",
        to_reference=node_to_builtin_transform(graph, node, profile_version, "Forward"),
        from_reference=node_to_builtin_transform(
            graph, node, profile_version, "Reverse"
        ),
        aliases=[],
    )

    return colorspace


def config_basename_aces(build_configuration):
    """
    Generate *aces-dev* reference implementation *OpenColorIO* config
    using the analytical *Graph* method basename.

    Parameters
    ----------
    build_configuration: BuildConfiguration
        Build configuration.

    Returns
    -------
    str
        *aces-dev* reference implementation *OpenColorIO* config using the
        analytical *Graph* method basename.
    """

    return ("reference-analytical-config_aces-{aces}_ocio-{ocio}.ocio").format(
        **build_configuration.compact_fields()
    )


def config_name_aces(build_configuration):
    """
    Generate *aces-dev* reference implementation *OpenColorIO* config
    using the analytical *Graph*  name.

    Parameters
    ----------
    build_configuration: BuildConfiguration
        Build configuration.

    Returns
    -------
    str
        *aces-dev* reference implementation *OpenColorIO* config using the
        analytical *Graph* method name.
    """

    return (
        "Academy Color Encoding System - Reference (Analytical) Config "
        "[ACES {aces}] "
        "[OCIO {ocio}]"
    ).format(**build_configuration.compact_fields())


def config_description_aces(build_configuration, describe=DescriptionStyle.SHORT_UNION):
    """
    Generate *aces-dev* reference implementation *OpenColorIO* config
    using the analytical *Graph* method description.

    Parameters
    ----------
    build_configuration: BuildConfiguration
        Build configuration.
    describe : int, optional
        Any value from the
        :class:`opencolorio_config_aces.DescriptionStyle` enum.

    Returns
    -------
    str
        *aces-dev* reference implementation *OpenColorIO* config using the
        analytical *Graph* method description.
    """

    name = config_name_aces(build_configuration)

    underline = "-" * len(name)

    summary = (
        'This "OpenColorIO" config is an analytical implementation of '
        '"aces-dev" and is designed to check whether the discovery process '
        "produces the expected output. It is not usable as it does not "
        'map to existing "OpenColorIO" builtin transforms.'
    )

    description = [name, underline, "", summary]

    if describe in ((DescriptionStyle.LONG_UNION,)):
        description.extend(["", timestamp()])

    return "\n".join(description)


def generate_config_aces(
    config_name=None,
    build_configuration=BuildConfiguration(),
    validate=True,
    describe=DescriptionStyle.LONG_UNION,
    filterers=None,
    additional_data=False,
):
    """
    Generate the *aces-dev* reference implementation *OpenColorIO* config
    using the analytical *Graph* method.

    The config generation is driven entirely from the *aces-dev* conversion
    graph. The config generated, while not usable because of the missing
    *OpenColorIO* *BuiltinTransforms*, provides an exact mapping with the
    *aces-dev* *CTL* transforms.

    Parameters
    ----------
    config_name : unicode, optional
        *OpenColorIO* config file name, if given the config will be written to
        disk.
    build_configuration: BuildConfiguration, optional
        Build configuration.
    validate : bool, optional
        Whether to validate the config.
    describe : int, optional
        Any value from the
        :class:`opencolorio_config_aces.DescriptionStyle` enum.
    filterers : array_like, optional
        List of callables used to filter the *ACES* *CTL* transforms, each
        callable takes an *ACES* *CTL* transform as argument and returns
        whether to include or exclude the *ACES* *CTL* transform as a bool.
    additional_data : bool, optional
        Whether to return additional data.

    Returns
    -------
    Config or tuple
        *OpenColorIO* config or tuple of *OpenColorIO* config,
        :class:`opencolorio_config_aces.ConfigData` class instance and dict of
        *OpenColorIO* colorspaces and
        :class:`opencolorio_config_aces.config.reference.CTLTransform` class
        instances.
    """

    LOGGER.info('Generating "%s" config...', config_name_aces(build_configuration))

    ctl_transforms = discover_aces_ctl_transforms()
    classified_ctl_transforms = classify_aces_ctl_transforms(ctl_transforms)
    filtered_ctl_transforms = filter_ctl_transforms(
        classified_ctl_transforms, filterers
    )

    graph = build_aces_conversion_graph(filtered_ctl_transforms)

    colorspaces_to_ctl_transforms = {}
    colorspaces = []
    display_names = set()
    views = []

    scene_reference_colorspace = colorspace_factory(
        f"CSC - {COLORSPACE_SCENE_ENCODING_REFERENCE}",
        "ACES",
        description='The "Academy Color Encoding System" reference colorspace.',
    )

    raw_colorspace = colorspace_factory(
        "Utility - Raw",
        "Utility",
        description='The utility "Raw" colorspace.',
        is_data=True,
    )

    colorspaces += [
        scene_reference_colorspace,
        raw_colorspace,
    ]

    LOGGER.info('Implicit colorspaces: "%s"', [a.getName() for a in colorspaces])

    for family in ("csc", "input_transform", "lmt", "output_transform"):
        family_colourspaces = []
        for node in filter_nodes(graph, [lambda x, family=family: x.family == family]):
            if node == COLORSPACE_SCENE_ENCODING_REFERENCE:
                continue

            LOGGER.info('Creating a colorspace for "%s" node...', node)
            colorspace = node_to_colorspace(
                graph, node, build_configuration.ocio, describe
            )

            family_colourspaces.append(colorspace)

            if family == "output_transform":
                display = (
                    f"Display"
                    f"{SEPARATOR_COLORSPACE_NAME}"
                    f"{beautify_display_name(node_to_ctl_transform(graph, node).genus)}"
                )
                display_names.add(display)
                view = beautify_view_name(colorspace.getName())
                views.append(
                    {
                        "display": display,
                        "view": view,
                        "colorspace": colorspace.getName(),
                    }
                )

            if additional_data:
                colorspaces_to_ctl_transforms[colorspace] = node_to_ctl_transform(
                    graph, node
                )

        colorspaces += family_colourspaces

    views = sorted(views, key=lambda x: (x["display"], x["view"]))
    display_names = sorted(display_names)
    if "sRGB" in display_names:
        display_names.insert(0, display_names.pop(display_names.index("sRGB")))

    for display_name in display_names:
        view = beautify_view_name(raw_colorspace.getName())
        LOGGER.info('Adding "%s" view to "%s" display.', view, display_name)
        views.append(
            {
                "display": display_name,
                "view": view,
                "colorspace": raw_colorspace.getName(),
            }
        )

    data = ConfigData(
        name=config_basename_aces(build_configuration),
        description=config_description_aces(build_configuration, describe),
        roles={
            ocio.ROLE_SCENE_LINEAR: "CSC - ACEScg",
        },
        colorspaces=colorspaces,
        views=views,
        active_displays=display_names,
        active_views=list(dict.fromkeys([view["view"] for view in views])),
        file_rules=[{"name": "Default", "colorspace": "CSC - ACEScg"}],
        profile_version=build_configuration.ocio,
    )

    config = generate_config(data, config_name, validate)

    LOGGER.info(
        '"%s" config generation complete!',
        config_name_aces(build_configuration),
    )

    if additional_data:
        return config, data, colorspaces_to_ctl_transforms
    else:
        return config


def main(build_directory):
    """
    Define the main entry point for the generation using the analytical *Graph*
    method of all the *aces-dev* reference implementation *OpenColorIO* config
    versions and variants.

    Parameters
    ----------
    build_directory : Path
        Build directory.

    Returns
    -------
    :class:`int`
        Return code.
    """

    LOGGER.info('Using "%s" build directory...', build_directory)

    build_directory.mkdir(parents=True, exist_ok=True)

    for build_configuration in BUILD_CONFIGURATIONS:
        config_basename = config_basename_aces(build_configuration)
        config, data, colorspaces = generate_config_aces(
            config_name=build_directory / config_basename,
            build_configuration=build_configuration,
            additional_data=True,
        )

        for ctl_transform in colorspaces.values():
            LOGGER.info(ctl_transform.aces_transform_id)

        # TODO: Pickling "PyOpenColorIO.ColorSpace" fails on early "PyOpenColorIO"
        # versions.
        try:
            serialize_config_data(
                data, build_directory / config_basename.replace("ocio", "json")
            )
        except TypeError as error:
            LOGGER.critical(error)

    return 0


if __name__ == "__main__":
    import sys

    from opencolorio_config_aces import serialize_config_data
    from opencolorio_config_aces.utilities import ROOT_BUILD_DEFAULT

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    sys.exit(main((ROOT_BUILD_DEFAULT / "config" / "aces" / "analytical").resolve()))
