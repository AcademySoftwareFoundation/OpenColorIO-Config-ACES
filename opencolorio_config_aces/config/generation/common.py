# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
OpenColorIO Config Generation Common Objects
============================================

Defines various objects related to *OpenColorIO* config generation:

-   :func:`opencolorio_config_aces.colorspace_factory`
-   :class:`opencolorio_config_aces.ConfigData`
-   :func:`opencolorio_config_aces.validate_config`
-   :func:`opencolorio_config_aces.generate_config`
"""

import logging

from opencolorio_config_aces.utilities import required, is_iterable

__author__ = 'OpenColorIO Contributors'
__copyright__ = 'Copyright Contributors to the OpenColorIO Project.'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'OpenColorIO Contributors'
__email__ = 'ocio-dev@lists.aswf.io'
__status__ = 'Production'

__all__ = [
    'LOG_ALLOCATION_VARS', 'colorspace_factory', 'ConfigData',
    'validate_config', 'generate_config'
]

LOG_ALLOCATION_VARS = (-8, 5, 2**-8)
"""
Allocation variables for logarithmic data representation.

LOG_ALLOCATION_VARS : tuple
"""


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
                       to_reference_transformation=None,
                       from_reference_transformation=None,
                       is_data=None,
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
    categories : array_like, optional
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
    to_reference_transformation : object, optional
        *To Reference* *OpenColorIO* colorspace transformation.
    from_reference_transformation : object, optional
        *From Reference* *OpenColorIO* colorspace transformation.
    is_data : bool, optional
        Whether the colorspace represents data.
    base_colorspace : ColorSpace, optional
        *OpenColorIO* base colorspace inherited for bit depth, allocation,
        allocation variables, and to/from reference transformations.

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

    if base_colorspace is not None:
        colorspace = base_colorspace
    else:
        colorspace = ocio.ColorSpace()

        colorspace.setBitDepth(bit_depth)

        if allocation is not None:
            colorspace.setAllocation(allocation)

        if allocation_vars is not None:
            colorspace.setAllocationVars(allocation_vars)

        if to_reference_transformation is not None:
            colorspace.setTransform(to_reference_transformation,
                                    ocio.COLORSPACE_DIR_TO_REFERENCE)

        if from_reference_transformation is not None:
            colorspace.setTransform(from_reference_transformation,
                                    ocio.COLORSPACE_DIR_FROM_REFERENCE)

    colorspace.setName(name)

    if family is not None:
        colorspace.setFamily(family)

    if encoding is not None:
        colorspace.setEncoding(encoding)

    for category in categories:
        colorspace.addCategory(category)

    if description is not None:
        colorspace.setDescription(description)

    if equality_group is not None:
        colorspace.setEqualityGroup(equality_group)

    if is_data is not None:
        colorspace.setIsData(is_data)

    return colorspace


class ConfigData:
    """
    Defines the data container for an *OpenColorIO* config.

    Parameters
    ----------
    roles : dict
        Config roles, a dict of role and colorspace name.
    colorspaces : array_like
        Config colorspaces, an iterable of
        :attr:`PyOpenColorIO.ColorSpace` class instances.
    views : array_like
        Config views, an iterable of dicts of display, view
        and colorspace names.
    active_displays : array_like
        Config active displays, an iterable of display names.
    active_views : array_like, optional
        Config active displays, an iterable of view names.
    file_rules : array_like, optional
        Config file rules, a dict of file rules.
    viewing_rules : array_like, optional
        Config viewing rules, a dict of viewing rules.
    description : unicode, optional
        Config description.
    profile_version : int, optional
        Config major version, i.e. 1 or 2.

    Attributes
    ----------
    roles
    colorspaces
    views
    active_displays
    active_views
    file_rules
    viewing_rules
    description
    profile_version
    """

    def __init__(self,
                 roles,
                 colorspaces,
                 views,
                 active_displays,
                 active_views=None,
                 file_rules=None,
                 viewing_rules=None,
                 description=None,
                 profile_version=None):
        self._roles = {}
        self.roles = roles
        self._colorspaces = []
        self.colorspaces = colorspaces
        self._views = []
        self.views = views
        self._active_displays = []
        self.active_displays = active_displays
        self._active_views = []
        self.active_views = active_views
        self._file_rules = []
        self.file_rules = file_rules
        self._viewing_rules = []
        self.viewing_rules = viewing_rules
        self._description = None
        self.description = description
        self._profile_version = 1
        self.profile_version = profile_version

    @property
    def roles(self):
        """
        Getter and setter property for the *OpenColorIO* config roles.

        Parameters
        ----------
        value : dict
            Attribute value.

        Returns
        -------
        dict
            *OpenColorIO* config roles.
        """

        return self._roles

    @roles.setter
    def roles(self, value):
        """
        Setter for **self.roles** property.
        """

        if value is not None:
            assert isinstance(value, dict), ((
                '"{0}" attribute: "{1}" is not a "dict" like object!').format(
                    'roles', value))
            self._roles = dict(value)

    @property
    def colorspaces(self):
        """
        Getter and setter property for the *OpenColorIO* config colorspaces.

        Parameters
        ----------
        value : array_like
            Attribute value.

        Returns
        -------
        list
            *OpenColorIO* config colorspaces.
        """

        return self._colorspaces

    @colorspaces.setter
    def colorspaces(self, value):
        """
        Setter for **self.colorspaces** property.
        """

        if value is not None:
            assert is_iterable(value), (
                ('"{0}" attribute: "{1}" is not an "array_like" like object!'
                 ).format('colorspaces', value))
            self._colorspaces = list(value)

    @property
    def views(self):
        """
        Getter and setter property for the *OpenColorIO* config views.

        Parameters
        ----------
        value : array_like
            Attribute value.

        Returns
        -------
        list
            *OpenColorIO* config views.
        """

        return self._views

    @views.setter
    def views(self, value):
        """
        Setter for **self.views** property.
        """

        if value is not None:
            assert is_iterable(value), (
                ('"{0}" attribute: "{1}" is not an "array_like" like object!'
                 ).format('views', value))
            self._views = list(value)

    @property
    def active_displays(self):
        """
        Getter and setter property for the *OpenColorIO* config active
        displays.

        Parameters
        ----------
        value : array_like
            Attribute value.

        Returns
        -------
        list
            *OpenColorIO* config active displays.
        """

        return self._active_displays

    @active_displays.setter
    def active_displays(self, value):
        """
        Setter for **self.active_displays** property.
        """

        if value is not None:
            assert is_iterable(value), (
                ('"{0}" attribute: "{1}" is not an "array_like" like object!'
                 ).format('active_displays', value))
            self._active_displays = list(value)

    @property
    def active_views(self):
        """
        Getter and setter property for the *OpenColorIO* config active views.

        Parameters
        ----------
        value : array_like
            Attribute value.

        Returns
        -------
        list
            *OpenColorIO* config active views.
        """

        return self._active_views

    @active_views.setter
    def active_views(self, value):
        """
        Setter for **self.active_views** property.
        """

        if value is not None:
            assert is_iterable(value), (
                ('"{0}" attribute: "{1}" is not an "array_like" like object!'
                 ).format('active_views', value))
            self._active_views = list(value)

    @property
    def file_rules(self):
        """
        Getter and setter property for the *OpenColorIO* config file rules.

        Parameters
        ----------
        value : array_like
            Attribute value.

        Returns
        -------
        list
            *OpenColorIO* config file rules.
        """

        return self._file_rules

    @file_rules.setter
    def file_rules(self, value):
        """
        Setter for **self.file_rules** property.
        """

        if value is not None:
            assert is_iterable(value), (
                ('"{0}" attribute: "{1}" is not an "array_like" like object!'
                 ).format('file_rules', value))
            self._file_rules = list(value)

    @property
    def viewing_rules(self):
        """
        Getter and setter property for the *OpenColorIO* config viewing rules.

        Parameters
        ----------
        value : array_like
            Attribute value.

        Returns
        -------
        list
            *OpenColorIO* config viewing rules.
        """

        return self._viewing_rules

    @viewing_rules.setter
    def viewing_rules(self, value):
        """
        Setter for **self.viewing_rules** property.
        """

        if value is not None:
            assert is_iterable(value), (
                ('"{0}" attribute: "{1}" is not an "array_like" like object!'
                 ).format('viewing_rules', value))
            self._viewing_rules = list(value)

    @property
    def description(self):
        """
        Getter and setter property for the *OpenColorIO* config description.

        Parameters
        ----------
        value : unicode
            Attribute value.

        Returns
        -------
        unicode
            *OpenColorIO* config description.
        """

        return self._description

    @description.setter
    def description(self, value):
        """
        Setter for **self.description** property.
        """

        if value is not None:
            assert isinstance(value, str), ((
                '"{0}" attribute: "{1}" is not a "str" like object!').format(
                    'description', value))
            self._description = value

    @property
    def profile_version(self):
        """
        Getter and setter property for the *OpenColorIO* config profile
        version.

        Parameters
        ----------
        value : int
            Attribute value.

        Returns
        -------
        int
            *OpenColorIO* config profile version.
        """

        return self._profile_version

    @profile_version.setter
    def profile_version(self, value):
        """
        Setter for **self.profile_version** property.
        """

        if value is not None:
            assert isinstance(value, int), ((
                '"{0}" attribute: "{1}" is not an "int" like object!').format(
                    'profile_version', value))
            self._profile_version = int(value)


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

    for colorspace, role in data.roles.items():
        logging.info(f'Adding "{colorspace}" colorspace as "{role}" role.')
        config.setRole(role, colorspace)

    for colorspace in data.colorspaces:
        logging.info(f'Adding colorspace "{colorspace.getName()}".')
        config.addColorSpace(colorspace)

    for view in data.views:
        display = view['display']
        view_name = view['view']
        colorspace = view.get('colorspace')
        looks = view.get('looks')
        view_transform = view.get('view_transform')
        rule = view.get('rule')
        description = view.get('rule')
        if colorspace:
            logging.info(f'Adding "{view_name}" view to "{display}" display '
                         f'using "{colorspace}" colorspace.')

            config.addDisplayView(display, view_name, colorspace, looks)
        else:
            logging.info(f'Adding "{view_name}" view to "{display}" display '
                         f'using "{view_transform}" view_transform, '
                         f'"{rule}" rule and "{description}" description.')

            config.addDisplayView(display, view_name, view_transform, looks,
                                  rule, description)

    config.setActiveDisplays(','.join(data.active_displays))
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
            logging.info(f'Setting "{name}" file rule with '
                         f'"{colorspace}" colorspace.')
            file_rules.setDefaultRuleColorSpace(colorspace)
        elif regex:
            logging.info(f'Adding "{name}" file rule with '
                         f'"{regex}" regex pattern for '
                         f'"{colorspace}" colorspace.')
            file_rules.insertRule(rule_index, name, colorspace, regex)
            rule_index += 1
        else:
            logging.info(f'Adding "{name}" file rule with '
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

    if validate:
        validate_config(config)

    if config_name is not None:
        with open(config_name, 'w') as file:
            file.write(config.serialize())

    return config


if __name__ == '__main__':
    required('OpenColorIO')(lambda: None)()

    import PyOpenColorIO as ocio

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    # "OpenColorIO 1" configuration.
    colorspace_1 = colorspace_factory('Gamut - sRGB', 'Gamut')

    colorspace_2 = colorspace_factory(
        'CCTF - sRGB',
        'CCTF',
        description=('WARNING: The sRGB "EOTF" is purposely incorrect and '
                     'only a placeholder!'),
        to_reference_transformation=ocio.ExponentTransform([2.2, 2.2, 2.2, 1]))

    colorspace_3 = colorspace_factory(
        'Colorspace - sRGB',
        'Colorspace',
        to_reference_transformation=ocio.ColorSpaceTransform(
            'CCTF - sRGB', 'Gamut - sRGB'))

    colorspace_4 = colorspace_factory(
        'View - sRGB Monitor - sRGB', 'View', base_colorspace=colorspace_3)

    colorspace_5 = colorspace_factory('Utility - Raw', 'Utility', is_data=True)

    data = ConfigData(
        roles={'Gamut - sRGB': ocio.ROLE_SCENE_LINEAR},
        colorspaces=[
            colorspace_1, colorspace_2, colorspace_3, colorspace_4,
            colorspace_5
        ],
        views=[
            {
                'display': 'sRGB Monitor',
                'view': 'sRGB - sRGB',
                'colorspace': 'View - sRGB Monitor - sRGB'
            },
            {
                'display': 'sRGB Monitor',
                'view': 'Raw',
                'colorspace': 'Utility - Raw'
            },
        ],
        active_displays=['sRGB Monitor'],
        active_views=['sRGB - sRGB'],
    )

    generate_config(data, 'config-v1.ocio')

    # "OpenColorIO 2" configuration.
    data.profile_version = 2
    transform = ocio.ExponentWithLinearTransform()
    transform.setGamma([2.4, 2.4, 2.4, 1])
    transform.setOffset([0.055, 0.055, 0.055, 0])
    data.colorspaces[1].setTransform(transform,
                                     ocio.COLORSPACE_DIR_TO_REFERENCE)
    data.colorspaces[1].setDescription('')

    # TODO: Use new display colorspace system.
    data.views = [
        {
            'display': 'sRGB Monitor',
            'view': 'sRGB - sRGB',
            'colorspace': 'View - sRGB Monitor - sRGB'
        },
        {
            'display': 'sRGB Monitor',
            'view': 'Raw',
            'colorspace': 'Utility - Raw'
        },
    ]
    data.file_rules = [
        {
            'name': 'Default',
            'colorspace': 'Gamut - sRGB'
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
    ]
    data.viewing_rules = []

    generate_config(data, 'config-v2.ocio')
