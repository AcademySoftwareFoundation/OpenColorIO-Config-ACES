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

import logging
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from pprint import pformat
from textwrap import indent

import PyOpenColorIO as ocio
from semver import Version

from opencolorio_config_aces.config.generation import PROFILE_VERSION_DEFAULT
from opencolorio_config_aces.utilities import DocstringDict, attest

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = [
    "BUILTIN_TRANSFORMS",
    "group_transform_factory",
    "colorspace_factory",
    "named_transform_factory",
    "view_transform_factory",
    "look_factory",
    "transform_factory_setter",
    "transform_factory_constructor",
    "transform_factory_clf_transform_to_group_transform",
    "TRANSFORM_FACTORIES",
    "transform_factory",
    "produce_transform",
]


BUILTIN_TRANSFORMS = DocstringDict(
    {
        builtin: PROFILE_VERSION_DEFAULT
        for builtin in ocio.BuiltinTransformRegistry()  # pyright: ignore
    }
)
BUILTIN_TRANSFORMS.__doc__ = """
Mapping of *OpenColorIO* builtintransforms to their profile version.

BUILTIN_TRANSFORMS : dict
"""

BUILTIN_TRANSFORMS.update(
    {
        "ACES-LMT - ACES 1.3 Reference Gamut Compression": Version(2, 1),
        "CURVE - CANON_CLOG2_to_LINEAR": Version(2, 2),
        "CURVE - CANON_CLOG3_to_LINEAR": Version(2, 2),
        "DISPLAY - CIE-XYZ-D65_to_DisplayP3": Version(2, 3),
    }
)


def group_transform_factory(transforms):
    """
    *OpenColorIO* `GroupTransform` factory.

    Parameters
    ----------
    transforms : array_like
        *OpenColorIO* transforms.

    Returns
    -------
    ocio.GroupTransform
        *OpenColorIO* `GroupTransform`.
    """

    logging.debug(
        'Producing a "GroupTransform" with the following transforms:\n%s',
        indent(pformat(locals()), "    "),
    )

    group_transform = ocio.GroupTransform()
    for transform in transforms:
        group_transform.appendTransform(produce_transform(transform))

    return group_transform


def colorspace_factory(
    name,
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
    **kwargs,
):
    """
    *OpenColorIO* `Colorspace` factory.

    Parameters
    ----------
    name : unicode
        *OpenColorIO* `Colorspace` name.
    family : unicode, optional
        *OpenColorIO* `Colorspace` family.
    encoding : unicode, optional
        *OpenColorIO* `Colorspace` encoding.
    aliases : unicode or array_like, optional
        *OpenColorIO* `Colorspace` aliases.
    categories : unicode or array_like, optional
        *OpenColorIO* `Colorspace` categories.
    description : unicode, optional
        *OpenColorIO* `Colorspace` description.
    equality_group : unicode, optional
        *OpenColorIO* `Colorspace` equality_group.
    bit_depth : int, optional
        *OpenColorIO* `Colorspace` bit depth.
    allocation : int, optional
        *OpenColorIO* `Colorspace` allocation type.
    allocation_vars : tuple, optional
        *OpenColorIO* `Colorspace` allocation variables.
    to_reference : dict or object, optional
        *To Reference* *OpenColorIO* transform.
    from_reference : dict or object, optional
        *From Reference* *OpenColorIO* transform.
    reference_space : unicode or ReferenceSpaceType, optional
        *OpenColorIO* `Colorspace` reference space.
    is_data : bool, optional
        Whether the `Colorspace` represents data.
    base_colorspace : dict or ColorSpace, optional
        *OpenColorIO* base `Colorspace` inherited for initial attribute values.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Keywords arguments.

    Returns
    -------
    ocio.ColorSpace
        *OpenColorIO* colorspace.
    """

    logging.debug(
        'Producing "%s" "ColorSpace" with the following parameters:\n%s',
        name,
        indent(pformat(locals()), "    "),
    )

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
                ocio.COLORSPACE_DIR_TO_REFERENCE,
            )

        if from_reference is not None:
            colorspace.setTransform(
                produce_transform(from_reference),
                ocio.COLORSPACE_DIR_FROM_REFERENCE,
            )

    colorspace.setName(name)

    if family is not None:
        colorspace.setFamily(family)

    if encoding is not None:
        colorspace.setEncoding(encoding)

    if aliases is not None:
        if isinstance(aliases, str):
            aliases = re.split("[,;]+", aliases)

        for alias in aliases:
            if not alias:
                continue

            colorspace.addAlias(alias)

    if categories is not None:
        if isinstance(categories, str):
            categories = re.split("[,;]+", categories)

        for category in categories:
            if not category:
                continue

            colorspace.addCategory(category)

    if description is not None:
        colorspace.setDescription(description)

    if equality_group is not None:
        colorspace.setEqualityGroup(equality_group)

    if is_data is not None:
        colorspace.setIsData(is_data)

    return colorspace


def named_transform_factory(
    name,
    family=None,
    encoding=None,
    aliases=None,
    categories=None,
    description=None,
    forward_transform=None,
    inverse_transform=None,
    base_named_transform=None,
    **kwargs,
):
    """
    *OpenColorIO* `NamedTransform` factory.

    Parameters
    ----------
    name : unicode
        *OpenColorIO* `NamedTransform` name.
    family : unicode, optional
        *OpenColorIO* `NamedTransform` family.
    encoding : unicode, optional
        *OpenColorIO* `NamedTransform` encoding.
    aliases : unicode or array_like, optional
        *OpenColorIO* `NamedTransform` aliases.
    categories : unicode or array_like, optional
        *OpenColorIO* `NamedTransform` categories.
    description : unicode, optional
        *OpenColorIO* `NamedTransform` description.
    forward_transform : dict or object, optional
        *Forward* *OpenColorIO* transform.
    inverse_transform : dict or object, optional
        *Inverse* *OpenColorIO* transform.
    base_named_transform : dict or NamedTransform, optional
        *OpenColorIO* base `NamedTransform` inherited for initial attribute
        values.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Keywords arguments.

    Returns
    -------
    ocio.NamedTransform
        *OpenColorIO* `NamedTransform`.
    """

    logging.debug(
        'Producing "%s" "NamedTransform" with the following parameters:\n%s',
        name,
        indent(pformat(locals()), "    "),
    )

    if base_named_transform is not None:
        if isinstance(base_named_transform, Mapping):
            base_named_transform = named_transform_factory(**base_named_transform)

        named_transform = base_named_transform
    else:
        named_transform = ocio.NamedTransform()

        if forward_transform is not None:
            named_transform.setTransform(
                produce_transform(forward_transform),
                ocio.TRANSFORM_DIR_FORWARD,
            )

        if inverse_transform is not None:
            named_transform.setTransform(
                produce_transform(inverse_transform),
                ocio.TRANSFORM_DIR_INVERSE,
            )

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
            categories = re.split("[,;]+", categories)

        for category in categories:
            named_transform.addCategory(category)

    if description is not None:
        named_transform.setDescription(description)

    return named_transform


def view_transform_factory(
    name,
    family=None,
    categories=None,
    description=None,
    to_reference=None,
    from_reference=None,
    reference_space=None,
    base_view_transform=None,
    **kwargs,
):
    """
    *OpenColorIO* `ViewTransform` factory.

    Parameters
    ----------
    name : unicode
        *OpenColorIO* `ViewTransform` name.
    family : unicode, optional
        *OpenColorIO* `ViewTransform` family.
    categories : array_like, optional
        *OpenColorIO* `ViewTransform` categories.
    description : unicode, optional
        *OpenColorIO* `ViewTransform` description.
    to_reference : dict or object, optional
        *To Reference* *OpenColorIO* `ViewTransform`.
    from_reference : dict or object, optional
        *From Reference* *OpenColorIO* `ViewTransform`.
    reference_space : unicode or ReferenceSpaceType, optional
        *OpenColorIO* `ViewTransform` reference space.
    base_view_transform : dict or ViewTransform, optional
        *OpenColorIO* base `ViewTransform` inherited for initial attribute
        values.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Keywords arguments.

    Returns
    -------
    ocio.ViewTransform
        *OpenColorIO* `ViewTransform`.
    """

    logging.debug(
        'Producing "%s" "ViewTransform" with the following parameters:\n%s',
        name,
        indent(pformat(locals()), "    "),
    )

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
                ocio.VIEWTRANSFORM_DIR_TO_REFERENCE,
            )

        if from_reference is not None:
            view_transform.setTransform(
                produce_transform(from_reference),
                ocio.VIEWTRANSFORM_DIR_FROM_REFERENCE,
            )

    view_transform.setName(name)

    if family is not None:
        view_transform.setFamily(family)

    for category in categories:
        view_transform.addCategory(category)

    if description is not None:
        view_transform.setDescription(description)

    return view_transform


def look_factory(
    name,
    process_space=None,
    description=None,
    forward_transform=None,
    inverse_transform=None,
    base_look=None,
    **kwargs,
):
    """
    *OpenColorIO* `Look` factory.

    Parameters
    ----------
    name : unicode
        *OpenColorIO* `Look` name.
    process_space : unicode, optional
        *OpenColorIO* `Look` process space, e.g., *OpenColorIO* `Colorspace` or
        role name.
    description : unicode, optional
        *OpenColorIO* `Look` description.
    forward_transform : dict or object, optional
        *To Reference* *OpenColorIO* `Look` transform.
    inverse_transform : dict or object, optional
        *From Reference* *OpenColorIO* `Look` transform.
    base_look : dict or ViewTransform, optional
        *OpenColorIO* base `Look` inherited for initial attribute values.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Keywords arguments.

    Returns
    -------
    ocio.Look
        *OpenColorIO* `Look`.
    """

    logging.debug(
        'Producing "%s" "Look" with the following parameters:\n%s',
        name,
        indent(pformat(locals()), "    "),
    )

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


def transform_factory_setter(**kwargs):
    """
    *OpenColorIO* default transform factory that produces an *OpenColorIO*
    transform according to given ``name`` keyword argument. The ``kwargs`` are
    set on the instance.

    Other Parameters
    ----------------
    name : unicode
        *OpenColorIO* transform class/type name, e.g., ``CDLTransform``.
    \\**kwargs : dict, optional
        Setter keywords arguments. They are converted to *camelCase* with *set*
        prepended, e.g., `base_colorspace` is transformed into
        `setBaseColorspace`.

    Returns
    -------
    object
        *OpenColorIO* transform.
    """

    transform = getattr(ocio, kwargs.pop("transform_type"))()

    kwargs.pop("transform_factory", None)

    logging.debug(
        'Producing a "%s" transform with the following parameters:\n%s',
        transform.__class__.__name__,
        indent(pformat(kwargs), "    "),
    )

    for kwarg, value in kwargs.items():
        method = re.sub(r"(?!^)_([a-zA-Z])", lambda m: m.group(1).upper(), kwarg)
        method = f"set{method[0].upper()}{method[1:]}"
        if hasattr(transform, method):
            getattr(transform, method)(value)

    return transform


def transform_factory_constructor(**kwargs):
    """
    *OpenColorIO* default transform factory that produces an *OpenColorIO*
    transform according to given ``name`` keyword argument. The ``kwargs`` are
    evaluated directly in the constructor.

    Other Parameters
    ----------------
    name : unicode
        *OpenColorIO* transform class/type name, e.g., ``CDLTransform``.
    \\**kwargs : dict, optional
        Keywords arguments that are evaluated directly in the constructor.

    Returns
    -------
    object
        *OpenColorIO* transform.
    """

    transform_type = kwargs.pop("transform_type")

    transform = getattr(ocio, transform_type)

    kwargs.pop("transform_factory", None)

    logging.debug(
        'Producing a "%s" transform with the following parameters:\n%s',
        transform_type,
        indent(pformat(kwargs), "    "),
    )

    return transform(**kwargs)


def transform_factory_clf_transform_to_group_transform(**kwargs):
    """
    *OpenColorIO* transform factory that produces an *OpenColorIO*
    `GroupTransform` if given ``name`` keyword argument is ``FileTransform`` and
    the ``src`` keyword argument is a *CLF* transform absolute path.

    Other Parameters
    ----------------
    name : unicode
        *OpenColorIO* ``FileTransform`` transform class.
    src : unicode
        *CLF* transform.

    Returns
    -------
    ocio.GroupTransform
        *OpenColorIO* `GroupTransform`.
    """

    attest(kwargs["transform_type"] == "FileTransform")
    attest(Path(kwargs["src"]).exists())

    logging.debug(
        'Producing a "FileTransform" transform with the following parameters:\n%s',
        indent(pformat(kwargs), "    "),
    )

    raw_config = ocio.Config().CreateRaw()
    file_transform = ocio.FileTransform(kwargs["src"])
    processor = raw_config.getProcessor(file_transform)

    return processor.createGroupTransform()


TRANSFORM_FACTORIES = DocstringDict(
    {
        "Setter": transform_factory_setter,
        "Constructor": transform_factory_constructor,
        "CLF Transform to Group Transform": (
            transform_factory_clf_transform_to_group_transform
        ),
    }
)
TRANSFORM_FACTORIES.__doc__ = """
*OpenColorIO* transform factories.

TRANSFORM_FACTORIES : dict
"""


def transform_factory(**kwargs):
    """
    *OpenColorIO* transform factory.

    Other Parameters
    ----------------
    factory : unicode
        {'Default', 'CLF Transform to `GroupTransform`'},
        *OpenColorIO* transform factory name.
    \\**kwargs : dict, optional
        Keywords arguments for the factory.

    Returns
    -------
    object
        *OpenColorIO* transform.
    """

    factory = TRANSFORM_FACTORIES[kwargs.get("transform_factory", "Setter")]

    return factory(**kwargs)


def produce_transform(transform):
    """
    Produce given transform.

    Parameters
    ----------
    transform : object or dict or array_like
        Transform to produce, either a single transform if a `Mapping`
        instance or a `GroupTransform` is a `Sequence` instance.

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
