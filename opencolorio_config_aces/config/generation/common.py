# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
OpenColorIO Config Generation Common Objects
============================================

Defines various objects related to *OpenColorIO* config generation:

-   :func:`opencolorio_config_aces.produce_transform`
-   :func:`opencolorio_config_aces.transform_factory`
-   :func:`opencolorio_config_aces.group_transform_factory`
-   :func:`opencolorio_config_aces.colorspace_factory`
-   :func:`opencolorio_config_aces.view_transform_factory`
-   :func:`opencolorio_config_aces.look_factory`
-   :class:`opencolorio_config_aces.ConfigData`
-   :class:`opencolorio_config_aces.serialize_config_data`
-   :class:`opencolorio_config_aces.deserialize_config_data`
-   :func:`opencolorio_config_aces.validate_config`
-   :func:`opencolorio_config_aces.generate_config`
"""

import json
import logging
import re
from collections import OrderedDict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Union

from opencolorio_config_aces.utilities import required

__author__ = 'OpenColorIO Contributors'
__copyright__ = 'Copyright Contributors to the OpenColorIO Project.'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'OpenColorIO Contributors'
__email__ = 'ocio-dev@lists.aswf.io'
__status__ = 'Production'

__all__ = [
    'LOG_ALLOCATION_VARS', 'produce_transform', 'transform_factory',
    'group_transform_factory', 'colorspace_factory', 'view_transform_factory',
    'look_factory', 'ConfigData', 'deserialize_config_data',
    'serialize_config_data', 'validate_config', 'generate_config'
]

LOG_ALLOCATION_VARS = (-8, 5, 2**-8)
"""
Allocation variables for logarithmic data representation.

LOG_ALLOCATION_VARS : tuple
"""


def produce_transform(transform):
    """
    Helper definition that produces given transform.

    Parameters
    ----------
    transform : object or dict or array_like
        Transform to produce, either a single transform if a `Mapping`
        instance or a group transform is a `Sequence` instance.

    Returns
    -------
    object
        *OpenColorIO* transform.
    """

    if isinstance(transform, Mapping):
        transform = transform_factory(**transform)
    elif isinstance(transform, Sequence):
        transform = group_transform_factory(transform)

    return transform


@required('OpenColorIO')
def transform_factory(name, **kwargs):
    """
    *OpenColorIO* transform factory.

    Parameters
    ----------
    name : unicode
        *OpenColorIO* transform class/type name, e.g. ``CDLTransform``.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Setter keywords arguments. They are converted to *camelCase* with *set*
        prepended, e.g. `base_colorspace` is transformed into
        `setBaseColorspace`.

    Returns
    -------
    object
        *OpenColorIO* transform.
    """

    import PyOpenColorIO as ocio

    transform = getattr(ocio, name)()
    for kwarg, value in kwargs.items():
        method = re.sub(r'(?!^)_([a-zA-Z])', lambda m: m.group(1).upper(),
                        kwarg)
        method = f'set{method[0].upper()}{method[1:]}'
        if hasattr(transform, method):
            getattr(transform, method)(value)

    return transform


@required('OpenColorIO')
def group_transform_factory(transforms):
    """
    *OpenColorIO* group transform factory.

    Parameters
    ----------
    transforms : array_like
        *OpenColorIO* transforms.

    Returns
    -------
    GroupTransform
        *OpenColorIO* group transform.
    """

    import PyOpenColorIO as ocio

    group_transform = ocio.GroupTransform()
    for transform in transforms:
        group_transform.appendTransform(produce_transform(transform))

    return group_transform


@required('OpenColorIO')
def colorspace_factory(name,
                       family=None,
                       encoding=None,
                       categories=None,
                       description=None,
                       equality_group=None,
                       bit_depth=None,
                       allocation=None,
                       allocation_vars=None,
                       to_reference=None,
                       from_reference=None,
                       is_data=None,
                       reference_space=None,
                       base_colorspace=None):
    """
    *OpenColorIO* colorspace factory.

    Parameters
    ----------
    name : unicode
        *OpenColorIO* colorspace name.
    family : unicode, optional
        *OpenColorIO* colorspace family.
    encoding : unicode, optional
        *OpenColorIO* colorspace encoding.
    categories : unicode or array_like, optional
        *OpenColorIO* colorspace categories.
    description : unicode, optional
        *OpenColorIO* colorspace description.
    equality_group : unicode, optional
        *OpenColorIO* colorspace equality_group.
    bit_depth : int, optional
        *OpenColorIO* colorspace bit depth.
    allocation : int, optional
        *OpenColorIO* colorspace allocation type.
    allocation_vars : tuple, optional
        *OpenColorIO* colorspace allocation variables.
    to_reference : dict or object, optional
        *To Reference* *OpenColorIO* colorspace transform.
    from_reference : dict or object, optional
        *From Reference* *OpenColorIO* colorspace transform.
    reference_space : unicode or ReferenceSpaceType, optional
        *OpenColorIO* colorspace reference space.
    is_data : bool, optional
        Whether the colorspace represents data.
    base_colorspace : dict or ColorSpace, optional
        *OpenColorIO* base colorspace inherited for bit depth, allocation,
        allocation variables, and to/from reference transforms.

    Returns
    -------
    ColorSpace
        *OpenColorIO* colorspace.
    """

    import PyOpenColorIO as ocio

    if categories is None:
        categories = []

    if bit_depth is None:
        bit_depth = ocio.BIT_DEPTH_F32

    if reference_space is None:
        reference_space = ocio.REFERENCE_SPACE_SCENE
    elif isinstance(reference_space, str):
        reference_space = getattr(ocio, reference_space)

    if base_colorspace is not None:
        if isinstance(base_colorspace, Mapping):
            base_colorspace = colorspace_factory(**base_colorspace)

        colorspace = base_colorspace
    else:
        colorspace = ocio.ColorSpace(reference_space)

        colorspace.setBitDepth(bit_depth)

        if allocation is not None:
            colorspace.setAllocation(allocation)

        if allocation_vars is not None:
            colorspace.setAllocationVars(allocation_vars)

        if to_reference is not None:
            colorspace.setTransform(
                produce_transform(to_reference),
                ocio.COLORSPACE_DIR_TO_REFERENCE)

        if from_reference is not None:
            colorspace.setTransform(
                produce_transform(from_reference),
                ocio.COLORSPACE_DIR_FROM_REFERENCE)

    colorspace.setName(name)

    if family is not None:
        colorspace.setFamily(family)

    if encoding is not None:
        colorspace.setEncoding(encoding)

    if categories is not None:
        if isinstance(categories, str):
            categories = re.split('[,;\\s]+', categories)

        for category in categories:
            colorspace.addCategory(category)

    if description is not None:
        colorspace.setDescription(description)

    if equality_group is not None:
        colorspace.setEqualityGroup(equality_group)

    if is_data is not None:
        colorspace.setIsData(is_data)

    return colorspace


@required('OpenColorIO')
def view_transform_factory(name,
                           family=None,
                           categories=None,
                           description=None,
                           to_reference=None,
                           from_reference=None,
                           reference_space=None,
                           base_view_transform=None):
    """
    *OpenColorIO* view transform factory.

    Parameters
    ----------
    name : unicode
        *OpenColorIO* view transform name.
    family : unicode, optional
        *OpenColorIO* view transform family.
    categories : array_like, optional
        *OpenColorIO* view transform categories.
    description : unicode, optional
        *OpenColorIO* view transform description.
    to_reference : dict or object, optional
        *To Reference* *OpenColorIO* view transform transform.
    from_reference : dict or object, optional
        *From Reference* *OpenColorIO* view transform transform.
    reference_space : unicode or ReferenceSpaceType, optional
        *OpenColorIO* view transform reference space.
    base_view_transform : dict or ViewTransform, optional
        Inherited *OpenColorIO* base view transform.

    Returns
    -------
    ViewTransform
        *OpenColorIO* view transform.
    """

    import PyOpenColorIO as ocio

    if categories is None:
        categories = []

    if reference_space is None:
        reference_space = ocio.REFERENCE_SPACE_SCENE
    elif isinstance(reference_space, str):
        reference_space = getattr(ocio, reference_space)

    if base_view_transform is not None:
        if isinstance(base_view_transform, Mapping):
            base_view_transform = view_transform_factory(**base_view_transform)

        view_transform = base_view_transform
    else:
        view_transform = ocio.ViewTransform(reference_space)

        if to_reference is not None:
            view_transform.setTransform(
                produce_transform(to_reference),
                ocio.VIEWTRANSFORM_DIR_TO_REFERENCE)

        if from_reference is not None:
            view_transform.setTransform(
                produce_transform(from_reference),
                ocio.VIEWTRANSFORM_DIR_FROM_REFERENCE)

    view_transform.setName(name)

    if family is not None:
        view_transform.setFamily(family)

    for category in categories:
        view_transform.addCategory(category)

    if description is not None:
        view_transform.setDescription(description)

    return view_transform


@required('OpenColorIO')
def look_factory(name,
                 process_space=None,
                 description=None,
                 forward_transform=None,
                 inverse_transform=None,
                 base_look=None):
    """
    *OpenColorIO* look factory.

    Parameters
    ----------
    name : unicode
        *OpenColorIO* look name.
    process_space : unicode, optional
        *OpenColorIO* look process space, e.g. *OpenColorIO* colorspace or role
        name.
    description : unicode, optional
        *OpenColorIO* look description.
    forward_transform : dict or object, optional
        *To Reference* *OpenColorIO* look transform.
    inverse_transform : dict or object, optional
        *From Reference* *OpenColorIO* look transform.
    base_look : dict or ViewTransform, optional
        Inherited *OpenColorIO* base look.

    Returns
    -------
    Look
        *OpenColorIO* look.
    """

    import PyOpenColorIO as ocio

    if process_space is None:
        process_space = ocio.ROLE_SCENE_LINEAR

    if base_look is not None:
        if isinstance(base_look, Mapping):
            base_look = look_factory(**base_look)

        look = base_look
    else:
        look = ocio.Look()

        look.setProcessSpace(process_space)

        if forward_transform is not None:
            look.setTransform(produce_transform(forward_transform))

        if inverse_transform is not None:
            look.setInverseTransform(produce_transform(inverse_transform))

    look.setName(name)

    if description is not None:
        look.setDescription(description)

    return look


@dataclass
class ConfigData:
    """
    Defines the data container for an *OpenColorIO* config.

    Parameters
    ----------
    profile_version : int, optional
        Config major version, i.e. 1 or 2.
    description : unicode, optional
        Config description.
    roles : dict
        Config roles, a dict of role and colorspace name.
    colorspaces : array_like
        Config colorspaces, an iterable of
        :attr:`PyOpenColorIO.ColorSpace` class instances.
    looks : array_like, optional
        Config looks, an iterable of :attr:`PyOpenColorIO.Look` class
        instances.
    view_transforms : array_like, optional
        Config view transforms, an iterable of
        :attr:`PyOpenColorIO.ViewTransform` class instances.
    shared_views : array_like, optional
        Config shared views, an iterable of dicts of view, view transform,
        colorspace and rule names, iterable of looks and description.
    views : array_like, optional
        Config views, an iterable of dicts of display, view
        and colorspace names.
    active_displays : array_like, optional
        Config active displays, an iterable of display names.
    active_views : array_like, optional
        Config active displays, an iterable of view names.
    file_rules : array_like, optional
        Config file rules, a dict of file rules.
    viewing_rules : array_like, optional
        Config viewing rules, a dict of viewing rules.
    inactive_colorspaces : array_like, optional
        Config inactive colorspaces an iterable of colorspace names.
    default_view_transform : unicode, optional
        Name of the default view transform.

    Attributes
    ----------
    schema_version
    profile_version
    description
    roles
    colorspaces
    looks
    view_transforms
    shared_views
    views
    active_displays
    active_views
    file_rules
    viewing_rules
    inactive_colorspaces
    default_view_transform
    """

    schema_version: int = 1
    profile_version: int = 1
    description: str = (
        'An "OpenColorIO" config generated by "OpenColorIO-Config-ACES".')
    roles: Union[dict, OrderedDict] = field(default_factory=dict)
    colorspaces: Union[list] = field(default_factory=list)
    looks: Union[list] = field(default_factory=list)
    view_transforms: Union[list] = field(default_factory=list)
    shared_views: Union[list] = field(default_factory=list)
    views: Union[list] = field(default_factory=list)
    active_displays: Union[list] = field(default_factory=list)
    active_views: Union[list] = field(default_factory=list)
    file_rules: Union[list] = field(default_factory=list)
    viewing_rules: Union[list] = field(default_factory=list)
    inactive_colorspaces: Union[list] = field(default_factory=list)
    default_view_transform: str = field(default_factory=str)


def deserialize_config_data(path):
    """
    Deserializes the *JSON* *OpenColorIO* config data container at given path.

    Parameters
    ----------
    path : unicode
        *JSON* file path.

    Returns
    -------
    ConfigData
        Deserialized *JSON* *OpenColorIO* config data container.
    """

    with open(path) as config_json:
        return ConfigData(**json.load(config_json))


# TODO: Implement schema verification support for serialized data.
def serialize_config_data(data, path):
    """
    Serializes the *OpenColorIO* config data container as a *JSON* file.

    Parameters
    ----------
    data : ConfigData
        *OpenColorIO* config data container to serialize.
    path : unicode
        *JSON* file path.
    """

    try:
        with open(path, 'w') as config_json:
            json.dump(asdict(data), config_json, indent=2)
    except Exception as error:
        logging.critical(
            f'Config data could not be serialised, please verify that you are '
            f'only using colorspace and transform signatures: {error}')


def validate_config(config):
    """
    Validates given *OpenColorIO* config.

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
        logging.critical(error)
        return False


@required('OpenColorIO')
def generate_config(data, config_name=None, validate=True):
    """
    Generates the *OpenColorIO* config from given data.

    Parameters
    ----------
    data : ConfigData
        *OpenColorIO* config data.
    config_name : unicode, optional
        *OpenColorIO* config file name, if given the config will be written to
        disk.
    validate : bool, optional
        Whether to validate the config.

    Returns
    -------
    Config
        *OpenColorIO* config.
    """

    import PyOpenColorIO as ocio

    config = ocio.Config()
    config.setMajorVersion(data.profile_version)

    if data.description is not None:
        config.setDescription(data.description)

    for role, colorspace in data.roles.items():
        logging.debug(f'Adding "{colorspace}" colorspace as "{role}" role.')
        config.setRole(role, colorspace)

    for colorspace in data.colorspaces:
        if isinstance(colorspace, Mapping):
            colorspace = colorspace_factory(**colorspace)

        logging.debug(f'Adding "{colorspace.getName()}" colorspace.')
        config.addColorSpace(colorspace)

    for view_transform in data.view_transforms:
        if isinstance(view_transform, Mapping):
            view_transform = view_transform_factory(**view_transform)

        logging.debug(f'Adding "{view_transform.getName()}" view transform.')
        config.addViewTransform(view_transform)

    for look in data.looks:
        if isinstance(look, Mapping):
            look = look_factory(**look)

        logging.debug(f'Adding "{look.getName()}" look.')
        config.addLook(look)

    if data.profile_version >= 2:
        logging.debug(f'Disabling "{data.inactive_colorspaces}" colorspaces.')
        config.setInactiveColorSpaces(','.join(data.inactive_colorspaces))

    for shared_view in data.shared_views:
        display_colorspace = shared_view.get('display_colorspace',
                                             '<USE_DISPLAY_NAME>')
        looks = shared_view.get('looks')
        view_transform = shared_view.get('view_transform')
        rule = shared_view.get('rule')
        description = shared_view.get('description')
        view = shared_view['view']
        logging.debug(
            f'Adding "{view}" shared view using "{view_transform}" '
            f'view transform, "{display_colorspace}" display colorspace, '
            f'"{looks}" looks, "{rule}" rule and "{description}"'
            f'description.')

        config.addSharedView(view, view_transform, display_colorspace, looks,
                             rule, description)

    for view in data.views:
        display = view['display']
        colorspace = view.get('colorspace')
        looks = view.get('looks')
        view_transform = view.get('view_transform')
        display_colorspace = view.get('display_colorspace')
        rule = view.get('rule')
        description = view.get('description')
        view = view['view']
        if colorspace is not None:
            logging.debug(f'Adding "{view}" view to "{display}" display '
                          f'using "{colorspace}" colorspace.')

            config.addDisplayView(display, view, colorspace, looks)
        elif view_transform is not None and display_colorspace is not None:
            logging.debug(f'Adding "{view}" view to "{display}" display '
                          f'using "{view_transform}" view transform, '
                          f'"{display_colorspace}" display colorspace, '
                          f'"{rule}" rule and "{description}" description.')

            config.addDisplayView(display, view, view_transform,
                                  display_colorspace, looks, rule, description)
        else:
            logging.debug(f'Adding "{view}" view to "{display}" display.')
            config.addDisplaySharedView(display, view)

    logging.debug(f'Activating "{data.active_displays}" displays.')
    config.setActiveDisplays(','.join(data.active_displays))

    logging.debug(f'Activating "{data.active_views}" views.')
    config.setActiveViews(','.join(data.active_views))

    file_rules = ocio.FileRules()
    rule_index = 0
    for file_rule in reversed(data.file_rules):
        name = file_rule['name']
        colorspace = file_rule['colorspace']
        regex = file_rule.get('regex')
        pattern = file_rule.get('pattern')
        extension = file_rule.get('extension')
        if name == 'Default':
            logging.debug(f'Setting "{name}" file rule with '
                          f'"{colorspace}" colorspace.')
            file_rules.setDefaultRuleColorSpace(colorspace)
        elif regex:
            logging.debug(f'Adding "{name}" file rule with '
                          f'"{regex}" regex pattern for '
                          f'"{colorspace}" colorspace.')
            file_rules.insertRule(rule_index, name, colorspace, regex)
            rule_index += 1
        else:
            logging.debug(f'Adding "{name}" file rule with '
                          f'"{pattern}" pattern and "{extension}" extension '
                          f'for "{colorspace}" colorspace.')
            file_rules.insertRule(rule_index, name, colorspace, pattern,
                                  extension)
            rule_index += 1
    config.setFileRules(file_rules)

    viewing_rules = ocio.ViewingRules()
    for i, viewing_rule in enumerate(reversed(data.viewing_rules)):
        logging.warning('Inserting a viewing rule is not supported yet!')
        # viewing_rules.insertRule()
    config.setViewingRules(viewing_rules)

    if data.default_view_transform is not None:
        config.setDefaultViewTransformName(data.default_view_transform)

    if validate:
        validate_config(config)

    if config_name is not None:
        with open(config_name, 'w') as file:
            file.write(config.serialize())

    return config


if __name__ == '__main__':
    required('OpenColorIO')(lambda: None)()

    import os
    import opencolorio_config_aces
    import PyOpenColorIO as ocio

    build_directory = os.path.join(opencolorio_config_aces.__path__[0], '..',
                                   'build')

    if not os.path.exists(build_directory):
        os.makedirs(build_directory)

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    # "OpenColorIO 1" configuration.
    colorspace_1 = {'name': 'Gamut - sRGB', 'family': 'Gamut'}
    colorspace_2 = {
        'name':
        'CCTF - sRGB',
        'family':
        'CCTF',
        'description': ('WARNING: The sRGB "EOTF" is purposely incorrect and '
                        'only a placeholder!'),
        'to_reference': {
            'name': 'ExponentTransform',
            'value': [2.2, 2.2, 2.2, 1],
        },
    }
    colorspace_3 = {
        'name': 'Colorspace - sRGB',
        'family': 'Colorspace',
        'to_reference': {
            'name': 'ColorSpaceTransform',
            'src': 'CCTF - sRGB',
            'dst': 'Gamut - sRGB',
        },
    }
    colorspace_4 = colorspace_factory(**{
        'name': 'Utility - Raw',
        'family': 'Utility',
        'is_data': True
    })

    _red_cdl_transform = ocio.CDLTransform()
    _red_cdl_transform.setSlope([0, 0, 0])
    _red_cdl_transform.setOffset([1, 0, 0])
    look_1 = look_factory('Look - Red', forward_transform=_red_cdl_transform)
    look_2 = {
        'name': 'Look - Green',
        'forward_transform': {
            'name': 'CDLTransform',
            'slope': [0, 0, 0],
            'offset': [0, 1, 0]
        }
    }
    _gain_cdl_transform = ocio.CDLTransform()
    _gain_cdl_transform.setSlope([0.5, 0.5, 0.5])
    look_3 = {
        'name':
        'Look - Quarter Blue',
        'forward_transform': [  # Note the nested "GroupTransform"s.
            [
                {
                    'name': 'CDLTransform',
                    'slope': [0, 0, 0],
                    'offset': [0, 1, 0]
                },
                _gain_cdl_transform,
            ],
            _gain_cdl_transform,
        ],
    }
    display_1 = {
        'name': 'View - sRGB Monitor - sRGB',
        'family': 'View',
        'base_colorspace': colorspace_3
    }

    data = ConfigData(
        roles={ocio.ROLE_SCENE_LINEAR: 'Gamut - sRGB'},
        colorspaces=[
            colorspace_1, colorspace_2, colorspace_3, colorspace_4, display_1
        ],
        looks=[look_1, look_2, look_3],
        views=[
            {
                'display': 'sRGB Monitor',
                'view': 'sRGB - sRGB',
                'colorspace': display_1['name'],
            },
            {
                'display': 'sRGB Monitor',
                'view': 'Raw',
                'colorspace': colorspace_4.getName(),
            },
        ],
        active_displays=['sRGB Monitor'],
        active_views=['sRGB - sRGB'],
    )

    generate_config(data, os.path.join(build_directory, 'config-v1.ocio'))

    # "OpenColorIO 2" configuration.
    colorspace_1 = {'name': 'ACES - ACES2065-1', 'family': 'ACES'}
    colorspace_2 = {
        'name': 'ACES - ACEScg',
        'family': 'ACES',
        'to_reference': {
            'name': 'BuiltinTransform',
            'style': 'ACEScg_to_ACES2065-1',
        },
    }
    colorspace_3 = {
        'name': 'Gamut - sRGB',
        'family': 'Gamut',
        'to_reference': {
            'name':
            'MatrixTransform',
            'matrix': [
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
        }
    }
    colorspace_4 = {
        'name': 'CCTF - sRGB',
        'family': 'CCTF',
        'to_reference': {
            'name': 'ExponentWithLinearTransform',
            'gamma': [2.4, 2.4, 2.4, 1],
            'offset': [0.055, 0.055, 0.055, 0],
        }
    }
    colorspace_5 = {
        'name': 'Utility - Raw',
        'family': 'Utility',
        'is_data': True
    }

    look_1 = {
        'name': 'Look - Red',
        'forward_transform': {
            'name': 'CDLTransform',
            'slope': [0, 0, 0],
            'offset': [1, 0, 0],
        }
    }

    interchange = {'name': 'CIE-XYZ D65'}

    display_1 = {
        'name': 'sRGB Monitor',
        'from_reference': {
            'name': 'BuiltinTransform',
            'style': 'DISPLAY - CIE-XYZ-D65_to_sRGB',
        },
        'reference_space': 'REFERENCE_SPACE_DISPLAY'
    }
    display_2 = {
        'name': 'ITU-R BT.1886 Monitor',
        'from_reference': {
            'name': 'BuiltinTransform',
            'style': 'DISPLAY - CIE-XYZ-D65_to_REC.1886-REC.709',
        },
        'reference_space': 'REFERENCE_SPACE_DISPLAY'
    }

    view_transform_1 = {
        'name': 'ACES Output - SDR Video - 1.0',
        'from_reference': {
            'name': 'BuiltinTransform',
            'style': 'ACES-OUTPUT - ACES2065-1_to_CIE-XYZ-D65 - SDR-VIDEO_1.0'
        },
    }
    view_transform_2 = {
        'name': 'Output - No Tonescale',
        'from_reference': {
            'name': 'BuiltinTransform',
            'style': 'UTILITY - ACES-AP0_to_CIE-XYZ-D65_BFD'
        },
    }

    displays = (display_1, display_2)
    view_transforms = (view_transform_1, view_transform_2)
    shared_views = [{
        'display': display['name'],
        'view': view_transform['name'],
        'view_transform': view_transform['name'],
    } for display in displays for view_transform in view_transforms]

    data = ConfigData(
        profile_version=2,
        roles={
            'aces_interchange': 'ACES - ACES2065-1',
            'cie_xyz_d65_interchange': 'CIE-XYZ D65',
            ocio.ROLE_SCENE_LINEAR: colorspace_2['name'],
        },
        colorspaces=[
            colorspace_1, colorspace_2, colorspace_3, colorspace_4,
            colorspace_5, interchange, display_1, display_2
        ],
        looks=[look_1],
        view_transforms=[view_transform_1, view_transform_2],
        inactive_colorspaces=['CIE-XYZ D65'],
        shared_views=shared_views,
        views=shared_views + [{
            'display': display['name'],
            'view': 'Raw',
            'colorspace': 'Utility - Raw'
        } for display in displays],
        active_displays=[display_1['name'], display_2['name']],
        active_views=[
            view_transform['name'] for view_transform in view_transforms
        ] + ['Raw'],
        file_rules=[
            {
                'name': 'Default',
                'colorspace': 'ACES - ACES2065-1'
            },
            {
                'name': 'Linear - sRGB',
                'colorspace': 'Gamut - sRGB',
                'regex': '_[sS][rR][gG][bB]\\.([eE][xX][rR]|[hH][dD][rR])$'
            },
            {
                'name': 'EOTF - sRGB',
                'colorspace': 'CCTF - sRGB',
                'regex': '_[sS][rR][gG][bB]\\.([pP][nN][gG]|[tT][iI][fF])$'
            },
        ],
        viewing_rules=[])

    generate_config(data, os.path.join(build_directory, 'config-v2.ocio'))

    serialize_config_data(data, os.path.join(build_directory,
                                             'config-v2.json'))
