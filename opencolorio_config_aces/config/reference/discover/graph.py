# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*aces-dev* Reference Implementation Conversion Graph
====================================================

Defines various objects related to *aces-dev* reference implementation
conversion graph:

-   :func:`opencolorio_config_aces.build_aces_conversion_graph`
-   :func:`opencolorio_config_aces.node_to_ctl_transform`
-   :func:`opencolorio_config_aces.ctl_transform_to_node`
-   :func:`opencolorio_config_aces.filter_nodes`
-   :func:`opencolorio_config_aces.conversion_path`
-   :func:`opencolorio_config_aces.plot_aces_conversion_graph`
"""

import codecs
import logging
import pickle
import networkx as nx

from opencolorio_config_aces.config.reference.discover.classify import (
    classify_aces_ctl_transforms, discover_aces_ctl_transforms,
    filter_ctl_transforms, unclassify_ctl_transforms)

__author__ = 'OpenColorIO Contributors'
__copyright__ = 'Copyright Contributors to the OpenColorIO Project.'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'OpenColorIO Contributors'
__email__ = 'ocio-dev@lists.aswf.io'
__status__ = 'Production'

__all__ = [
    'NODE_NAME_SEPARATOR', 'build_aces_conversion_graph',
    'node_to_ctl_transform', 'ctl_transform_to_node', 'filter_nodes',
    'conversion_path', 'plot_aces_conversion_graph'
]

NODE_NAME_SEPARATOR = '/'
"""
*aces-dev* conversion graph node name separator.

NODE_NAME_SEPARATOR : unicode
"""


def build_aces_conversion_graph(ctl_transforms):
    """
    Builds the *aces-dev* conversion graph from given *ACES* *CTL* transforms.

    Parameters
    ----------
    ctl_transforms : dict or list
        *ACES* *CTL* transforms as returned by
        :func:`opencolorio_config_aces.classify_aces_ctl_transforms`,
        :func:`opencolorio_config_aces.unclassify_aces_ctl_transforms` or
        :func:`opencolorio_config_aces.filter_ctl_transforms` definitions.

    Returns
    -------
    DiGraph
        *aces-dev* conversion graph.

    Examples
    --------
    >>> ctl_transforms = classify_aces_ctl_transforms(
    ...     discover_aces_ctl_transforms())
    >>> build_aces_conversion_graph(ctl_transforms)  # doctest: +ELLIPSIS
    <networkx.classes.digraph.DiGraph object at 0x...>
    """

    if isinstance(ctl_transforms, dict):
        ctl_transforms = unclassify_ctl_transforms(ctl_transforms)

    ctl_transforms = sorted(ctl_transforms, key=lambda x: x.path)

    graph = nx.DiGraph()

    for ctl_transform in ctl_transforms:
        source = ctl_transform.source
        target = ctl_transform.target
        family = ctl_transform.family
        type_ = ctl_transform.type

        if source is None or target is None:
            logging.debug(f'"{ctl_transform}" has either a missing source '
                          f'or target colourspace and won\'t be included in '
                          f'the "aces-dev" conversion graph!')
            continue

        # Without enforcing a preferred source and target colourspaces, the
        # nodes do not necessarily have predictable source and target
        # colourspaces which might be confusing, e.g. a node for an
        # "Output Transform" might have an "RGBmonitor_100nits_dim" source and
        # a "OCES" target.
        if family in ('csc', 'input_transform', 'lmt'):
            if source == 'ACES2065-1':
                logging.debug(f'"{ctl_transform}" ctl transform from the '
                              f'"{family}" family uses "{source}" as source, '
                              f'skipping!')
                continue
        elif family == 'output_transform':
            if target in ('ACES2065-1', 'OCES'):
                logging.debug(f'"{ctl_transform}" ctl transform from the '
                              f'"{family}" family uses "{target}" as target, '
                              f'skipping!')
                continue

        source = (source if source in ('ACES2065-1', 'OCES') else
                  f'{type_}{NODE_NAME_SEPARATOR}{source}')
        target = (target if target in ('ACES2065-1', 'OCES') else
                  f'{type_}{NODE_NAME_SEPARATOR}{target}')

        # Serializing the data for "Graphviz AGraph".
        serialized = codecs.encode(pickle.dumps(ctl_transform, 4),
                                   'base64').decode()

        for node in (source, target):
            if node not in graph.nodes():
                graph.add_node(node, data=ctl_transform, serialized=serialized)
            else:
                logging.debug(f'"{node}" node was already added to '
                              f'the "aces-dev" conversion graph '
                              f'by the "{node_to_ctl_transform(graph, node)}" '
                              f'"CTL" transform, skipping!')

        graph.add_edge(source, target)

    return graph


def node_to_ctl_transform(graph, node):
    """
    Returns the *ACES* *CTL* transform from given node name.

    Parameters
    ----------
    graph : DiGraph
        *aces-dev* conversion graph.
    node : unicode
        Node name to return the *ACES* *CTL* transform from.

    Returns
    -------
    CTLTransform
        *ACES* *CTL* transform.

    Examples
    --------
    >>> ctl_transforms = classify_aces_ctl_transforms(
    ...     discover_aces_ctl_transforms())
    >>> graph = build_aces_conversion_graph(ctl_transforms)
    >>> node_to_ctl_transform(graph, 'ODT/P3D60_48nits')  # doctest: +ELLIPSIS
    CTLTransform('odt...p3...ODT.Academy.P3D60_48nits.ctl')
    """

    return graph.nodes[node]['data']


def ctl_transform_to_node(graph, ctl_transform):
    """
    Returns the node name from given *ACES* *CTL* transform.

    Parameters
    ----------
    graph : DiGraph
        *aces-dev* conversion graph.
    ctl_transform : CTLTransform
        *ACES* *CTL* transform to return the node name from.

    Returns
    -------
    unicode
        Node name.

    Examples
    --------
    >>> ctl_transforms = classify_aces_ctl_transforms(
    ...     discover_aces_ctl_transforms())
    >>> graph = build_aces_conversion_graph(ctl_transforms)
    >>> ctl_transform = node_to_ctl_transform(graph, 'ODT/P3D60_48nits')
    >>> ctl_transform_to_node(graph, ctl_transform)
    'ODT/P3D60_48nits'
    """

    for node in graph.nodes:
        if node_to_ctl_transform(graph, node) == ctl_transform:
            return node


def filter_nodes(graph, filterers=None):
    """
    Filters given *aces-dev* conversion graph nodes with given filterers.

    Parameters
    ----------
    graph : DiGraph
        *aces-dev* conversion graph.
    filterers : array_like, optional
        List of callables used to filter the *ACES* *CTL* transforms, each
        callable takes an *ACES* *CTL* transform as argument and returns
        whether to include or exclude the *ACES* *CTL* transform as a bool.

    Returns
    -------
    list
        Filtered *aces-dev* conversion graph nodes.

    Examples
    --------
    >>> ctl_transforms = classify_aces_ctl_transforms(
    ...     discover_aces_ctl_transforms())
    >>> graph = build_aces_conversion_graph(ctl_transforms)
    >>> sorted(filter_nodes(graph, [lambda x: x.genus == 'p3']))[0]
    'ODT/P3D60_48nits'
    """

    if filterers is None:
        filterers = []

    filtered_nodes = []
    for node in graph.nodes:
        included = True
        for filterer in filterers:
            included *= filterer(node_to_ctl_transform(graph, node))

        if included:
            filtered_nodes.append(node)

    return filtered_nodes


def conversion_path(graph, source, target):
    """
    Returns the conversion path from the source node to the target node in the
    *aces-dev* conversion graph.

    Parameters
    ----------
    graph : DiGraph
        *aces-dev* conversion graph.
    source : unicode
        Source node.
    target : unicode
        Target node.

    Returns
    -------
    list
        Conversion path from the source node to the target node.

    Examples
    --------
    >>> ctl_transforms = classify_aces_ctl_transforms(
    ...     discover_aces_ctl_transforms())
    >>> graph = build_aces_conversion_graph(ctl_transforms)
    >>> conversion_path(graph, 'IDT/Venice_SLog3_SGamut3', 'ODT/P3D60_48nits')
    [('IDT/Venice_SLog3_SGamut3', 'ACES2065-1'), ('ACES2065-1', 'OCES'), \
('OCES', 'ODT/P3D60_48nits')]
    """

    path = nx.shortest_path(graph, source, target)

    return [(a, b) for a, b in zip(path[:-1], path[1:])]


def plot_aces_conversion_graph(graph, filename, prog='dot', args=''):
    """
    Plots given *aces-dev* conversion graph using
    `Graphviz <https://www.graphviz.org/>`__ and
    `pyraphviz <https://pygraphviz.github.io>`__.

    Parameters
    ----------
    graph : DiGraph
        *aces-dev* conversion graph.
    filename : unicode
        Filename to use to save the image.
    prog : unicode, optional
        {'neato', 'dot', 'twopi', 'circo', 'fdp', 'nop'},
        *Graphviz* layout method.
    args : unicode, optional
         Additional arguments for *Graphviz*.

    Returns
    -------
    AGraph
        *PyGraphviz* graph.
    """

    agraph = nx.nx_agraph.to_agraph(graph)

    agraph.node_attr.update(
        style='filled', shape='circle', fontname='Helvetica', fontsize=20)

    ctl_transforms_csc = []
    ctl_transforms_idt = []
    ctl_transforms_odt = []
    ctl_transforms_output_transform = []
    ctl_transforms_lmt = []

    for node in agraph.nodes():
        unserialized = pickle.loads(
            codecs.decode(node.attr['serialized'].encode(), 'base64'))

        ctl_transform_type = unserialized.type
        if node in ('ACES2065-1', 'OCES'):
            node.attr.update(
                shape='doublecircle',
                color='#673AB7FF',
                fillcolor='#673AB770',
                fontsize=30)
        elif ctl_transform_type == 'ACEScsc':
            node.attr.update(color='#00BCD4FF', fillcolor='#00BCD470')
            ctl_transforms_csc.append(node)
        elif ctl_transform_type == 'IDT':
            node.attr.update(color='#B3BC6D', fillcolor='#E6EE9C')
            ctl_transforms_idt.append(node)
        elif ctl_transform_type in ('ODT', 'InvODT'):
            node.attr.update(color='#CA9B52', fillcolor='#FFCC80')
            ctl_transforms_odt.append(node)
        elif ctl_transform_type in ('RRTODT', 'InvRRTODT'):
            node.attr.update(color='#C88719', fillcolor='#FFB74D')
            ctl_transforms_output_transform.append(node)
        elif ctl_transform_type == 'LMT':
            node.attr.update(color='#4BA3C7', fillcolor='#81D4FA')
            ctl_transforms_lmt.append(node)

    agraph.add_subgraph(
        ctl_transforms_csc, name='cluster_ACEScsc', color='#00BCD4FF')
    agraph.add_subgraph(
        ctl_transforms_idt, name='cluster_IDT', color='#B3BC6D')
    agraph.add_subgraph(
        ctl_transforms_odt, name='cluster_ODT', color='#CA9B52')
    agraph.add_subgraph(
        ctl_transforms_output_transform,
        name='cluster_OutputTransform',
        color='#C88719')
    agraph.add_subgraph(
        ctl_transforms_lmt, name='cluster_LMT', color='#4BA3C7')

    agraph.edge_attr.update(color='#26323870')
    agraph.draw(filename, prog=prog, args=args)

    return agraph


if __name__ == '__main__':
    import os
    import subprocess
    import opencolorio_config_aces
    from pprint import pprint
    from opencolorio_config_aces.utilities import message_box

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    build_directory = os.path.join(opencolorio_config_aces.__path__[0], '..',
                                   'build')

    if not os.path.exists(build_directory):
        os.makedirs(build_directory)

    filename = os.path.join(build_directory, 'aces_conversion_graph.png')

    ctl_transforms = discover_aces_ctl_transforms()
    classified_ctl_transforms = classify_aces_ctl_transforms(ctl_transforms)
    filtered_ctl_transforms = filter_ctl_transforms(classified_ctl_transforms)

    graph = build_aces_conversion_graph(filtered_ctl_transforms)
    print(graph.nodes)

    message_box('Retrieving a "CTL" Transform from a Node')
    print(node_to_ctl_transform(graph, 'ODT/P3D60_48nits'))

    message_box('Retrieving a Node from a "CTL" Transform')
    print(
        ctl_transform_to_node(graph,
                              node_to_ctl_transform(graph,
                                                    'ODT/P3D60_48nits')))

    message_box('Filtering "output_transform" Family')
    pprint(
        filter_nodes(
            graph,
            [lambda x: True if x.family == 'output_transform' else False]))

    message_box('Filtering "p3" Genus')
    pprint(filter_nodes(graph, [lambda x: True if x.genus == 'p3' else False]))

    plot_aces_conversion_graph(graph, filename)

    try:
        os.startfile(filename, 'open')
    except AttributeError:
        subprocess.call(['open', filename])
