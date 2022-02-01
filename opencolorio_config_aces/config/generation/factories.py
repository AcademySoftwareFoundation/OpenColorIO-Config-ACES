# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
OpenColorIO Config Generation Transform Factories
=================================================

Defines various *OpenColorIO* transform factories:

-   :func:`opencolorio_config_aces.group_transform_factory`
-   :func:`opencolorio_config_aces.colorspace_factory`
-   :func:`opencolorio_config_aces.named_transform_factory`
-   :func:`opencolorio_config_aces.view_transform_factory`
-   :func:`opencolorio_config_aces.look_factory`
-   :func:`opencolorio_config_aces.transform_factory`
-   :func:`opencolorio_config_aces.produce_transform`
"""

import re
from pathlib import Path
from typing import Mapping, Sequence

from opencolorio_config_aces.utilities import required

__author__ = 'OpenColorIO Contributors'
__copyright__ = 'Copyright Contributors to the OpenColorIO Project.'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'OpenColorIO Contributors'
__email__ = 'ocio-dev@lists.aswf.io'
__status__ = 'Production'

__all__ = [
    'group_transform_factory', 'colorspace_factory', 'named_transform_factory',
    'view_transform_factory', 'look_factory', 'transform_factory_default',
    'transform_factory_clf_transform_to_group_transform',
    'TRANSFORM_FACTORIES', 'transform_factory', 'produce_transform'
]


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
                       aliases=None,
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
                       base_colorspace=None,
                       **kwargs):
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
    aliases : unicode or array_like, optional
        *OpenColorIO* colorspace aliases.
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
        *OpenColorIO* base colorspace inherited for initial attribute values.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Keywords arguments.

    Returns
    -------
    ColorSpace
        *OpenColorIO* colorspace.
    """

    import PyOpenColorIO as ocio

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

    if aliases is not None:
        if isinstance(aliases, str):
            aliases = [aliases]

        for alias in aliases:
            colorspace.addAlias(alias)

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
def named_transform_factory(name,
                            family=None,
                            encoding=None,
                            aliases=None,
                            categories=None,
                            description=None,
                            forward_transform=None,
                            inverse_transform=None,
                            base_named_transform=None,
                            **kwargs):
    """
    *OpenColorIO* named transform factory.

    Parameters
    ----------
    name : unicode
        *OpenColorIO* colorspace name.
    family : unicode, optional
        *OpenColorIO* colorspace family.
    encoding : unicode, optional
        *OpenColorIO* colorspace encoding.
    aliases : unicode or array_like, optional
        *OpenColorIO* colorspace aliases.
    categories : unicode or array_like, optional
        *OpenColorIO* colorspace categories.
    description : unicode, optional
        *OpenColorIO* colorspace description.
    forward_transform : dict or object, optional
        *Forward* *OpenColorIO* transform.
    inverse_transform : dict or object, optional
        *Inverse* *OpenColorIO* transform.
    base_named_transform : dict or NamedTransform, optional
        *OpenColorIO* base named transform inherited for initial attribute
        values.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Keywords arguments.

    Returns
    -------
    NamedTransform
        *OpenColorIO* named transform.
    """

    import PyOpenColorIO as ocio

    if base_named_transform is not None:
        if isinstance(base_named_transform, Mapping):
            base_named_transform = named_transform_factory(
                **base_named_transform)

        named_transform = base_named_transform
    else:
        named_transform = ocio.NamedTransform()

        if forward_transform is not None:
            named_transform.setTransform(
                produce_transform(forward_transform),
                ocio.TRANSFORM_DIR_FORWARD)

        if inverse_transform is not None:
            named_transform.setTransform(
                produce_transform(inverse_transform),
                ocio.TRANSFORM_DIR_INVERSE)

    named_transform.setName(name)

    if family is not None:
        named_transform.setFamily(family)

    if encoding is not None:
        named_transform.setEncoding(encoding)

    if aliases is not None:
        if isinstance(aliases, str):
            aliases = [aliases]

        for alias in aliases:
            named_transform.addAlias(alias)

    if categories is not None:
        if isinstance(categories, str):
            categories = re.split('[,;\\s]+', categories)

        for category in categories:
            named_transform.addCategory(category)

    if description is not None:
        named_transform.setDescription(description)

    return named_transform


@required('OpenColorIO')
def view_transform_factory(name,
                           family=None,
                           categories=None,
                           description=None,
                           to_reference=None,
                           from_reference=None,
                           reference_space=None,
                           base_view_transform=None,
                           **kwargs):
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
        *To Reference* *OpenColorIO* view transform.
    from_reference : dict or object, optional
        *From Reference* *OpenColorIO* view transform.
    reference_space : unicode or ReferenceSpaceType, optional
        *OpenColorIO* view transform reference space.
    base_view_transform : dict or ViewTransform, optional
        *OpenColorIO* base view transform inherited for initial attribute
        values.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Keywords arguments.

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
                 base_look=None,
                 **kwargs):
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
        *OpenColorIO* base look inherited for initial attribute values.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Keywords arguments.

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


@required('OpenColorIO')
def transform_factory_default(**kwargs):
    """
    *OpenColorIO* default transform factory that produces an *OpenColorIO*
    transform according to given ``name`` keyword argument.

    Other Parameters
    ----------------
    name : unicode
        *OpenColorIO* transform class/type name, e.g. ``CDLTransform``.
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

    transform = getattr(ocio, kwargs.pop('transform_type'))()
    for kwarg, value in kwargs.items():
        method = re.sub(r'(?!^)_([a-zA-Z])', lambda m: m.group(1).upper(),
                        kwarg)
        method = f'set{method[0].upper()}{method[1:]}'
        if hasattr(transform, method):
            getattr(transform, method)(value)

    return transform


@required('OpenColorIO')
def transform_factory_clf_transform_to_group_transform(**kwargs):
    """
    *OpenColorIO* transform factory that produces an *OpenColorIO*
    group transform if given ``name`` keyword argument is ``FileTransform`` and
    the ``src`` keyword argument is a *CLF* transform absolute path.

    Other Parameters
    ----------------
    name : unicode
        *OpenColorIO* ``FileTransform`` transform class.
    src : unicode
        *CLF* transform.

    Returns
    -------
    GroupTransform
        *OpenColorIO* group transform.
    """

    import PyOpenColorIO as ocio

    assert kwargs['transform_type'] == 'FileTransform'
    assert Path(kwargs['src']).exists()

    raw_config = ocio.Config().CreateRaw()
    file_transform = ocio.FileTransform(kwargs['src'])
    processor = raw_config.getProcessor(file_transform)

    return processor.createGroupTransform()


TRANSFORM_FACTORIES = {
    'Default':
    transform_factory_default,
    'CLF Transform to Group Transform':
    transform_factory_clf_transform_to_group_transform,
}
"""
*OpenColorIO* transform factories.

TRANSFORM_FACTORIES : dict
"""


def transform_factory(**kwargs):
    """
    *OpenColorIO* transform factory.

    Other Parameters
    ----------------
    factory : unicode
        {'Default', 'CLF Transform to Group Transform'},
        *OpenColorIO* transform factory name.
    \\**kwargs : dict, optional
        Keywords arguments for the factory.

    Returns
    -------
    object
        *OpenColorIO* transform.
    """

    factory = TRANSFORM_FACTORIES[kwargs.get('transform_factory', 'Default')]

    return factory(**kwargs)


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
