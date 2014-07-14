"Utilites for sorting."

# Copyright (C) 2008-2014 Johan Hake
#
# This file is part of UFL.
#
# UFL is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# UFL is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with UFL. If not, see <http://www.gnu.org/licenses/>.

from six import itervalues, iteritems

def topological_sorting(nodes, edges):
    """
    Return a topologically sorted list of the nodes

    Implemented algorithm from Wikipedia :P

    <http://en.wikipedia.org/wiki/Topological_sorting>

    No error for cyclic edges...
    """

    L = []
    S = nodes[:]
    for node in nodes:
        for es in itervalues(edges):
            if node in es and node in S:
                S.remove(node)
                continue

    while S:
        node = S.pop(0)
        L.append(node)
        node_edges = edges[node]
        while node_edges:
            m = node_edges.pop(0)
            found = False
            for es in itervalues(edges):
                found = m in es
                if found:
                    break
            if not found:
                S.insert(0, m)

    return L

def sorted_by_count(seq):
    "Sort a sequence by the item.count()."
    return sorted(seq, key=lambda x: x.count())

def sorted_by_key(mapping):
    "Sort dict items by key, allowing different key types."
    # Python3 doesn't allow comparing builtins of different type, therefore the typename trick here
    return sorted(iteritems(mapping), key=lambda x: (type(x[0]).__name__, x[0]))
