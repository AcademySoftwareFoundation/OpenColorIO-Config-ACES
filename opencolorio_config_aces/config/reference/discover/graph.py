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
import re

from opencolorio_config_aces.config.reference.discover.classify import (
    classify_aces_ctl_transforms,
    discover_aces_ctl_transforms,
    filter_ctl_transforms,
    unclassify_ctl_transforms,
)
from opencolorio_config_aces.utilities import required

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = [
    "SEPARATOR_NODE_NAME_CTL",
    "build_aces_conversion_graph",
    "node_to_ctl_transform",
    "ctl_transform_to_node",
    "filter_nodes",
    "conversion_path",
    "plot_aces_conversion_graph",
]

logger = logging.getLogger(__name__)

SEPARATOR_NODE_NAME_CTL = "/"
"""
*aces-dev* conversion graph node name separator.

SEPARATOR_NODE_NAME_CTL : unicode
"""


@required("NetworkX")
def build_aces_conversion_graph(ctl_transforms):
    """
    Build the *aces-dev* conversion graph from given *ACES* *CTL* transforms.

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

    import networkx as nx

    if isinstance(ctl_transforms, dict):
        ctl_transforms = unclassify_ctl_transforms(ctl_transforms)

    ctl_transforms = sorted(ctl_transforms, key=lambda x: x.path)

    graph = nx.DiGraph()

    for ctl_transform in ctl_transforms:
        source = ctl_transform.source
        target = ctl_transform.target
        type_ = ctl_transform.type

        if source is None or target is None:
            logger.debug(
                '"%s" has either a missing source or target colourspace and '
                'won\'t be included in the "aces-dev" conversion graph!',
                ctl_transform,
            )
            continue

        # Special case for "Look" family whose transformations source and target
        # are both "ACES2065-1".
        if source == "ACES2065-1" and type_ == "Look":
            source = ctl_transform.name
        elif target == "ACES2065-1" and type_ == "InvLook":
            target = ctl_transform.name

        source = (
            source
            if source == "ACES2065-1"
            else f"{type_}{SEPARATOR_NODE_NAME_CTL}{source}"
        )
        source = re.sub("^Inv", "", source)

        target = (
            target
            if target == "ACES2065-1"
            else f"{type_}{SEPARATOR_NODE_NAME_CTL}{target}"
        )
        target = re.sub("^Inv", "", target)

        # Serializing the data for "Graphviz AGraph".
        serialized = codecs.encode(pickle.dumps(ctl_transform, 4), "base64").decode()

        for node in (source, target):
            if node not in graph.nodes():
                graph.add_node(node, data=ctl_transform, serialized=serialized)
            else:
                logger.debug(
                    '"%s" node was already added to the "aces-dev" '
                    'conversion graph by the "%s" "CTL" transform, skipping!',
                    node,
                    node_to_ctl_transform(graph, node),
                )

        graph.add_edge(source, target)

    return graph


def node_to_ctl_transform(graph, node):
    """
    Return the *ACES* *CTL* transform from given node name.

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
    >>> node_to_ctl_transform(graph, "Output/P3D60")  # doctest: +ELLIPSIS
    CTLTransform('aces-output...p3...Output.Academy.P3D60.ctl')
    """

    return graph.nodes[node]["data"]


def ctl_transform_to_node(graph, ctl_transform):
    """
    Return the node name from given *ACES* *CTL* transform.

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
    >>> ctl_transform = node_to_ctl_transform(graph, "Output/P3D60")
    >>> ctl_transform_to_node(graph, ctl_transform)
    'Output/P3D60'
    """

    for node in graph.nodes:
        if node_to_ctl_transform(graph, node) == ctl_transform:
            return node

    return None


def filter_nodes(graph, filterers=None):
    """
    Filter given *aces-dev* conversion graph nodes with given filterers.

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
    >>> sorted(filter_nodes(graph, [lambda x: x.genus == "p3"]))[0]
    'Output/P3D60'
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


@required("NetworkX")
def conversion_path(graph, source, target):
    """
    Return the conversion path from the source node to the target node in the
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
    >>> conversion_path(graph, "CSC/Venice_SLog3_SGamut3", "Output/P3D60")
    [('CSC/Venice_SLog3_SGamut3', 'ACES2065-1'), ('ACES2065-1', 'Output/P3D60')]
    """

    import networkx as nx

    path = nx.shortest_path(graph, source, target)

    return list(zip(path[:-1], path[1:]))


@required("NetworkX")
def plot_aces_conversion_graph(graph, filename, prog="dot", args=""):
    """
    Plot given *aces-dev* conversion graph using
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

    import networkx as nx

    agraph = nx.nx_agraph.to_agraph(graph)

    agraph.node_attr.update(
        style="filled", shape="circle", fontname="Helvetica", fontsize=20
    )

    ctl_transforms_csc = []
    ctl_transforms_output = []
    ctl_transforms_look = []

    for node in agraph.nodes():
        unserialized = pickle.loads(  # noqa: S301
            codecs.decode(node.attr["serialized"].encode(), "base64")
        )

        ctl_transform_type = unserialized.type
        if node == "ACES2065-1":
            node.attr.update(
                shape="doublecircle",
                color="#673AB7FF",
                fillcolor="#673AB770",
                fontsize=30,
            )
        elif ctl_transform_type == "CSC":
            node.attr.update(color="#00BCD4FF", fillcolor="#00BCD470")
            ctl_transforms_csc.append(node)
        elif ctl_transform_type in ("Look", "InvLook"):
            node.attr.update(color="#4BA3C7", fillcolor="#81D4FA")
            ctl_transforms_look.append(node)
        elif ctl_transform_type in ("Output", "InvOutput"):
            node.attr.update(color="#CA9B52", fillcolor="#FFCC80")
            ctl_transforms_output.append(node)

    agraph.add_subgraph(ctl_transforms_csc, name="cluster_CSC", color="#00BCD4FF")
    agraph.add_subgraph(ctl_transforms_look, name="cluster_Look", color="#4BA3C7")
    agraph.add_subgraph(ctl_transforms_output, name="cluster_Output", color="#CA9B52")

    agraph.edge_attr.update(color="#26323870")
    agraph.draw(filename, prog=prog, args=args)

    return agraph


if __name__ == "__main__":
    from pprint import pformat

    from opencolorio_config_aces.utilities import ROOT_BUILD_DEFAULT, message_box

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    build_directory = (ROOT_BUILD_DEFAULT / "aces" / "graph").resolve()

    logger.info('Using "%s" build directory...', build_directory)

    build_directory.mkdir(parents=True, exist_ok=True)

    filename = build_directory / "aces_conversion_graph.svg"

    ctl_transforms = discover_aces_ctl_transforms()
    classified_ctl_transforms = classify_aces_ctl_transforms(ctl_transforms)
    filtered_ctl_transforms = filter_ctl_transforms(classified_ctl_transforms)

    graph = build_aces_conversion_graph(filtered_ctl_transforms)
    logger.info(graph.nodes)

    message_box('Retrieving a "CTL" Transform from a Node', print_callable=logger.info)
    logger.info(node_to_ctl_transform(graph, "Output/P3D60"))

    message_box('Retrieving a Node from a "CTL" Transform', print_callable=logger.info)
    logger.info(
        ctl_transform_to_node(graph, node_to_ctl_transform(graph, "Output/P3D60"))
    )

    message_box('Filtering "Output" Family', print_callable=logger.info)
    logger.info(
        pformat(
            filter_nodes(
                graph,
                [lambda x: x.family == "output"],
            )
        )
    )

    message_box('Filtering "p3" Genus', print_callable=logger.info)
    logger.info(pformat(filter_nodes(graph, [lambda x: x.genus == "p3"])))

    plot_aces_conversion_graph(graph, filename)
