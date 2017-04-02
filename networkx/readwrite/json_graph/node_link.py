#    Copyright (C) 2011-2016 by
# 
#    Aric Hagberg <hagberg@lanl.gov>
#    Dan Schult <dschult@colgate.edu>
#    Pieter Swart <swart@lanl.gov>
#    Michael E. Rose <Michael.Ernst.Rose@gmail.com>
#    
#    All rights reserved.
#    BSD license.
from itertools import chain, count
import json
import networkx as nx
from networkx.utils import make_str, to_tuple
from tempfile import NamedTemporaryFile
__all__ = ['node_link_data', 'node_link_graph']


_attrs = dict(source='source', target='target', name='name',
              key='key', link='links')


def node_link_data(G, attrs=None):
    """Return data in node-link format that is suitable for JSON serialization
    and use in Javascript documents.

    Parameters
    ----------
    G : NetworkX graph

    attrs : dict
        A dictionary that contains five keys 'source', 'target', 'name',
        'key' and 'link'.  The corresponding values provide the attribute
        names for storing NetworkX-internal graph data.  The values should
        be unique.  Default value::

            dict(source='source', target='target', name='name',
                 key='key', link='links')

        If some user-defined graph data use these attribute names as data keys,
        they may be silently dropped.

    Returns
    -------
    data : dict
       A dictionary with node-link formatted data.

    Raises
    ------
    NetworkXError
        If values in attrs are not unique.

    Examples
    --------
    >>> from networkx.readwrite import json_graph
    >>> G = nx.Graph([('A', 'B')])
    >>> data1 = json_graph.node_link_data(G)
    >>> H = nx.gn_graph(2)
    >>> data2 = json_graph.node_link_data(H, {'link': 'edges', 'source': 'from', 'target': 'to'})    

    To serialize with json

    >>> import json
    >>> s1 = json.dumps(data1)
    >>> s2 = json.dumps(data2, default={'link': 'edges', 'source': 'from', 'target': 'to'})

    Notes
    -----
    Graph, node, and link attributes are stored in this format.  Note that
    attribute keys will be converted to strings in order to comply with JSON.

    Attribute 'key' is only used for multigraphs.

    See Also
    --------
    node_link_graph, adjacency_data, tree_data
    """
    multigraph = G.is_multigraph()
    # Allow 'attrs' to keep default values.
    if attrs is None:
        attrs = _attrs
    else:
        attrs.update({k: v for (k, v) in _attrs.items() if k not in attrs})
    name = attrs['name']
    source = attrs['source']
    target = attrs['target']
    links = attrs['link']
    # Allow 'key' to be omitted from attrs if the graph is not a multigraph.
    key = None if not multigraph else attrs['key']
    if len(set([source, target, key])) < 3:
        raise nx.NetworkXError('Attribute names are not unique.')
    mapping = dict(zip(G, count()))
    data = {}
    data['directed'] = G.is_directed()
    data['multigraph'] = multigraph
    data['graph'] = G.graph
    data['nodes'] = [dict(chain(G.node[n].items(), [(name, n)])) for n in G]
    if multigraph:
        data[links] = [
            dict(chain(d.items(),
                       [(source, mapping[u]), (target, mapping[v]), (key, k)]))
            for u, v, k, d in G.edges(keys=True, data=True)]
    else:
        data[links] = [
            dict(chain(d.items(),
                       [(source, mapping[u]), (target, mapping[v])]))
            for u, v, d in G.edges(data=True)]
    return data


def node_link_graph(data, directed=False, multigraph=True, attrs=None):
    """Return graph from node-link data format.

    Parameters
    ----------
    data : dict
        node-link formatted graph data

    directed : bool
        If True, and direction not specified in data, return a directed graph.

    multigraph : bool
        If True, and multigraph not specified in data, return a multigraph.

    attrs : dict
        A dictionary that contains five keys 'source', 'target', 'name',
        'key' and 'link'.  The corresponding values provide the attribute
        names for storing NetworkX-internal graph data.  Default value:

            dict(source='source', target='target', name='name',
                key='key', link='links')

    Returns
    -------
    G : NetworkX graph
        A NetworkX graph object

    Examples
    --------
    >>> from networkx.readwrite import json_graph
    >>> G = nx.Graph([('A', 'B')])
    >>> data = json_graph.node_link_data(G)
    >>> H = json_graph.node_link_graph(data)

    Notes
    -----
    Attribute 'key' is only used for multigraphs.

    See Also
    --------
    node_link_data, adjacency_data, tree_data
    """
    # Allow 'attrs' to keep default values.
    if attrs is None:
        attrs = _attrs
    else:
        attrs.update({k: v for (k, v) in _attrs.iteritems() if k not in attrs})
    multigraph = data.get('multigraph', multigraph)
    directed = data.get('directed', directed)
    if multigraph:
        graph = nx.MultiGraph()
    else:
        graph = nx.Graph()
    if directed:
        graph = graph.to_directed()
    name = attrs['name']
    source = attrs['source']
    target = attrs['target']
    links = attrs['link']
    # Allow 'key' to be omitted from attrs if the graph is not a multigraph.
    key = None if not multigraph else attrs['key']
    mapping = []
    graph.graph = data.get('graph', {})
    c = count()
    for d in data['nodes']:
        node = to_tuple(d.get(name, next(c)))
        mapping.append(node)
        nodedata = dict((make_str(k), v) for k, v in d.items() if k != name)
        graph.add_node(node, **nodedata)
    for d in data[links]:
        src = d[source]
        tgt = d[target]
        if not multigraph:
            edgedata = dict((make_str(k), v) for k, v in d.items()
                            if k != source and k != target)
            graph.add_edge(mapping[src], mapping[tgt], **edgedata)
        else:
            ky = d.get(key, None)
            edgedata = dict((make_str(k), v) for k, v in d.items()
                            if k != source and k != target and k != key)
            graph.add_edge(mapping[src], mapping[tgt], ky, **edgedata)
    return graph
