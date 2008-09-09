"This module contains a collection of common utilities."

__authors__ = "Martin Sandve Alnes and Anders Logg"
__date__ = "2008-08-05 -- 2008-08-26"

import operator

def product(sequence):
    "Return the product of all elements in a sequence."
    return reduce(operator.__mul__, sequence, 1)

def some_key(a_dict):
    "Return an arbitrary key from a dictionary."
    return zip((0,), a_dict.iterkeys())[0][1]

class Counted(object):
    """A class of objects identified by a global counter.
    
    Requires that the subclass has a class variable
    _globalcount = 0"""
    __slots__ = ("_count",)
    def __init__(self, count = None):
        if count is None:
            self._count = self.__class__._globalcount
            self.__class__._globalcount += 1
        else:
            self._count = count
            if count >= self.__class__._globalcount:
                self.__class__._globalcount = count + 1


class Stack(list):
    "A stack datastructure."
    def __init__(self, *args):
        list.__init__(self, *args)
    
    def push(self, v):
        list.append(self, v)
    
    def peek(self):
        return self[-1]


class StackDict(dict):
    "A dict that can be changed incrementally with 'd.push(k,v)' and have changes rolled back with 'k,v = d.pop()'."
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self._l = []
    
    def push(self, k, v):
        self._l.append((k, self.get(k, None)))
        self[k] = v
    
    def pop(self):
        k, v = self._l.pop()
        if v is None:
            del self[k]
        else:
            self[k] = v
        return k, v

def strides(shape):
    if len(shape) == 0:
        return ()
    stride = 1
    result = [1]
    for s in shape[-1:0:-1]:
        stride *= s
        result.append(stride)
    return tuple(reversed(result))

def component_to_index(component, shape):
    i = 0
    for (c,s) in zip(component, strides(shape)):
        i += c*s
    return i

def index_to_component(index, shape):
    component = []
    for s in strides(shape):
        a = index // s
        b = index % s
        index = b
        component.append(a)
    return tuple(component)

def test_component_indexing():
    print
    s = ()
    print s, strides(s)
    c = ()
    q = component_to_index(c, s)
    c2 = index_to_component(q, s)
    print c, q, c2

    print
    s = (2,)
    print s, strides(s)
    for i in range(s[0]):
        c = (i,)
        q = component_to_index(c, s)
        c2 = index_to_component(q, s)
        print c, q, c2

    print
    s = (2,3)
    print s, strides(s)
    for i in range(s[0]):
        for j in range(s[1]):
            c = (i,j)
            q = component_to_index(c, s)
            c2 = index_to_component(q, s)
            print c, q, c2

    print
    s = (2,3,4)
    print s, strides(s)
    for i in range(s[0]):
        for j in range(s[1]):
            for k in range(s[2]):
                c = (i,j,k)
                q = component_to_index(c, s)
                c2 = index_to_component(q, s)
                print c, q, c2

    # Taylor-Hood example:

    # pressure element is index 3:
    c = (3,)
    # get flat index:
    i = component_to_index(c, (4,))
    # remove offset:
    i -= 3
    # map back to component:
    c = index_to_component(i, ())
    print c

    # vector element y-component is index 1:
    c = (1,)
    # get flat index:
    i = component_to_index(c, (4,))
    # remove offset:
    i -= 0
    # map back to component:
    c = index_to_component(i, (3,))
    print c

    # Try a tensor/vector element:
    mixed_shape = (6,)
    ts = (2,2)
    vs = (2,)
    offset = 4

    # vector element y-component is index offset+1:
    c = (offset+1,)
    # get flat index:
    i = component_to_index(c, mixed_shape)
    # remove offset:
    i -= offset
    # map back to vector component:
    c = index_to_component(i, vs)
    print c

    for k in range(4):
        # tensor element (1,1)-component is index 3:
        c = (k,)
        # get flat index:
        i = component_to_index(c, mixed_shape)
        # remove offset:
        i -= 0
        # map back to vector component:
        c = index_to_component(i, ts)
        print c

def test_stackdict():
    d = StackDict(a=1)
    d.push("a", 2)
    d.push("a", 3)
    print d
    d.pop()
    print d
    d.pop()
    print d

if __name__ == "__main__":
    test_component_indexing()
    test_stackdict()
