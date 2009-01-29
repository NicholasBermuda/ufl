"Basic algebra operations."

__authors__ = "Martin Sandve Alnes"
__date__ = "2008-05-20 -- 2009-01-28"

# Modified by Anders Logg, 2008

from collections import defaultdict
from itertools import chain

from ufl.log import error, warning
from ufl.assertions import ufl_assert
from ufl.common import product, mergedicts, subdict
from ufl.expr import Expr
from ufl.zero import Zero
from ufl.scalar import ScalarValue, FloatValue, IntValue, is_true_ufl_scalar, is_python_scalar, as_ufl
from ufl.indexing import IndexBase, Index, FixedIndex
from ufl.indexutils import unique_indices
from ufl.sorting import cmp_expr

#--- Algebraic operators ---

class Sum(Expr):
    __slots__ = ("_operands", "_repr")
    
    def __new__(cls, *operands): # TODO: This seems a bit complicated... Can it be simplified? Maybe we can merge some loops for efficiency?
        ufl_assert(len(operands), "Can't take sum of nothing.")
        
        # make sure everything is an Expr
        operands = [as_ufl(o) for o in operands]
        
        # assert consistent tensor properties
        sh = operands[0].shape()
        fi = set(operands[0].free_indices())
        fid = set(operands[0].index_dimensions())
        ufl_assert(all(sh == o.shape() for o in operands[1:]),
            "Shape mismatch in Sum.")
        ufl_assert(not any((fi ^ set(o.free_indices())) for o in operands[1:]),
            "Can't add expressions with different free indices.")
        
        # sort operands in a canonical order
        operands = sorted(operands, cmp=cmp_expr)
        
        # purge zeros
        operands = [o for o in operands if not isinstance(o, Zero)]
        
        # sort scalars to beginning and merge them
        scalars = [o for o in operands if isinstance(o, ScalarValue)]
        if scalars:
            # exploiting Pythons built-in coersion rules
            f = as_ufl(sum(f._value for f in scalars))
            nonscalars = [o for o in operands if not isinstance(o, ScalarValue)]
            if not nonscalars:
                return f
            if isinstance(f, Zero):
                operands = nonscalars
            else:
                operands = [f] + nonscalars
        
        # have we purged everything? 
        if not operands:
            return Zero(sh, tuple(fi), fid)
        
        # left with one operand only?
        if len(operands) == 1:
            return operands[0]
        
        # Replace n-repeated operands foo with n*foo
        newoperands = []
        op = operands[0]
        n = 1
        for o in operands[1:] + [None]:
            if o == op:
                n += 1
            else:
                newoperands.append(op if n == 1 else n*op)
                op = o
                n = 1
        operands = newoperands
        
        # left with one operand only?
        if len(operands) == 1:
            return operands[0]
        
        # construct and initialize a new Sum object
        self = Expr.__new__(cls)
        self._init(*operands)
        return self

    def _init(self, *operands):
        ufl_assert(all(isinstance(o, Expr) for o in operands), "Expecting Expr instances.")
        self._operands = operands
        self._repr = "Sum(%s)" % ", ".join(repr(o) for o in operands)
    
    def __init__(self, *operands):
        Expr.__init__(self)
    
    def operands(self):
        return self._operands
    
    def free_indices(self):
        return self._operands[0].free_indices()
    
    def index_dimensions(self):
        return self._operands[0].index_dimensions()
    
    def shape(self):
        return self._operands[0].shape()
    
    def evaluate(self, x, mapping, component, index_values):
        return sum(o.evaluate(x, mapping, component, index_values) for o in self.operands())
    
    def __str__(self):
        return "(%s)" % " + ".join(str(o) for o in self._operands)
    
    def __repr__(self):
        return self._repr

class Product(Expr):
    """The product of two or more UFL objects."""
    __slots__ = ("_operands", "_free_indices", "_index_dimensions", "_shape", "_repr")
    
    def __new__(cls, *operands):
        # Got one operand only? Do nothing then.
        if len(operands) == 1:
            return operands[0]
        
        # Assert valid input types
        ufl_assert(len(operands) >= 2, "Can't make product of nothing, should catch this before getting here.")
        operands = [as_ufl(o) for o in operands]
        
        # Sort operands in a canonical order (NB! This is fragile! Small changes here can have large effects.)
        operands = sorted(operands, cmp=cmp_expr)
        
        # Get shape and move an eventual single nonscalar operand to the end
        sh = ()
        j = None
        for i, o in enumerate(operands):
            sh2 = o.shape()
            if sh2 != ():
                ufl_assert(sh == (), "Found two nonscalar operands in Product, this is undefined.")
                sh = sh2
                j = i
        if j is not None:
            # We have a non-scalar expression in this product
            operands = operands[:j] + operands[j+1:] + [operands[j]]
        
        # Check for zeros
        if any(isinstance(o, Zero) for o in operands):
            free_indices = unique_indices(tuple(chain(*(o.free_indices() for o in operands))))
            index_dimensions = mergedicts([o.index_dimensions() for o in operands])
            return Zero(sh, free_indices, index_dimensions)
        
        # Replace n-repeated operands foo with foo**n (as long as they have no free indices)
        # TODO: Maybe we can support u[i]**n now, since IndexSum was introduced. Then we get u[i]*u[i] => sum_i< u[i]**2 >
        newoperands = []
        op = operands[0]
        n = 1
        for o in operands[1:] + [None]:
            if o == op:
                n += 1
            else:
                if n == 1:
                    newoperands.append(op)
                elif op.free_indices():
                    newoperands.extend([op]*n)
                else:
                    newoperands.append(op**n)
                op = o
                n = 1
        operands = newoperands
        
        # Left with one operand only?
        if len(operands) == 1:
            return operands[0]
        
        # Merge scalars, but keep nonscalars sorted
        scalars = [o for o in operands if isinstance(o, ScalarValue)]
        if scalars:
            p = as_ufl(product(s._value for s in scalars))
            nonscalars = [o for o in operands if not isinstance(o, ScalarValue)]
            if not nonscalars:
                return p
            if p == 1:
                operands = nonscalars
            else:
                operands = [p] + nonscalars
        
        # left with one operand only?
        if len(operands) == 1:
            return operands[0]
        
        # construct and initialize a new Product object
        self = Expr.__new__(cls)
        self._init(sh, *operands)
        return self
    
    def _init(self, sh, *operands):
        "Constructor, called by __new__ with already checked arguments."
        # Store basic properties
        self._operands = operands
        self._shape = sh
        
        # Extract indices
        self._free_indices = unique_indices(tuple(chain(*(o.free_indices() for o in operands))))
        self._index_dimensions = mergedicts([o.index_dimensions() for o in operands])
        
        self._repr = "Product(%s)" % ", ".join(repr(o) for o in self._operands)
    
    def __init__(self, *operands):
        Expr.__init__(self)
    
    def operands(self):
        return self._operands
    
    def free_indices(self):
        return self._free_indices
    
    def index_dimensions(self):
        return self._index_dimensions
    
    def shape(self):
        return self._shape
    
    def evaluate(self, x, mapping, component, index_values):
        ufl_assert(self.shape() == (), "FIXME")
        return product(o.evaluate(x, mapping, component, index_values) for o in self.operands())
    
    def __str__(self):
        return "(%s)" % " * ".join(str(o) for o in self._operands)
    
    def __repr__(self):
        return self._repr

class Division(Expr):
    __slots__ = ("_a", "_b")
    
    def __new__(cls, a, b):
        a = as_ufl(a)
        b = as_ufl(b)

        ufl_assert(b != 0, "Division by zero!")
        ufl_assert(is_true_ufl_scalar(b), "Division by non-scalar.")
        
        if isinstance(a, Zero):
            return a
        
        # TODO: Handling int/int specially here to avoid "2/3 == 0", do we want this?
        if isinstance(a, IntValue) and isinstance(b, IntValue):
            return as_ufl(a._value / float(b._value))
        
        if isinstance(a, ScalarValue) and isinstance(b, ScalarValue):
            return as_ufl(a._value / b._value)
        
        # construct and initialize a new Division object
        self = Expr.__new__(cls)
        self._init(a, b)
        return self
    
    def _init(self, a, b):
        ufl_assert(all(isinstance(o, Expr) for o in (a, b)), "Expecting Expr instances.")
        self._a = a
        self._b = b

    def __init__(self, a, b):
        Expr.__init__(self)
    
    def operands(self):
        return (self._a, self._b)
    
    def free_indices(self):
        return self._a.free_indices()
    
    def index_dimensions(self):
        return self._a.index_dimensions()
    
    def shape(self):
        return self._a.shape()
    
    def evaluate(self, x, mapping, component, index_values):    
        a, b = self.operands()
        a = a.evaluate(x, mapping, component, index_values)
        b = b.evaluate(x, mapping, component, index_values)
        return a/b
    
    def __str__(self):
        return "(%s / %s)" % (str(self._a), str(self._b))
    
    def __repr__(self):
        return "Division(%r, %r)" % (self._a, self._b)

class Power(Expr):
    __slots__ = ("_a", "_b")
    
    def __new__(cls, a, b):
        a = as_ufl(a)
        b = as_ufl(b)
        if not (is_true_ufl_scalar(a) and is_true_ufl_scalar(b)):
            print 
            print "Non-scalar power error:"
            print a
            print b
            print "TODO: Maybe we can support this."
            print 
        
        ufl_assert(is_true_ufl_scalar(a) and is_true_ufl_scalar(b),
            "Non-scalar power not defined.")
        if isinstance(a, ScalarValue) and isinstance(b, ScalarValue):
            return as_ufl(a._value ** b._value)
        if b == 1:
            return a
        if b == 0:
            return IntValue(1)
        
        # construct and initialize a new Power object
        self = Expr.__new__(cls)
        self._init(a, b)
        return self
    
    def _init(self, a, b):
        ufl_assert(all(isinstance(o, Expr) for o in (a, b)), "Expecting Expr instances.")
        self._a = a
        self._b = b

    def __init__(self, a, b):
        Expr.__init__(self)
    
    def operands(self):
        return (self._a, self._b)
    
    def free_indices(self):
        return ()
    
    def index_dimensions(self):
        return {}
    
    def shape(self):
        return ()
    
    def evaluate(self, x, mapping, component, index_values):    
        a, b = self.operands()
        a = a.evaluate(x, mapping, component, index_values)
        b = b.evaluate(x, mapping, component, index_values)
        return a**b
    
    def __str__(self):
        return "(%s ** %s)" % (str(self._a), str(self._b))
    
    def __repr__(self):
        return "Power(%r, %r)" % (self._a, self._b)

class Abs(Expr):
    __slots__ = ("_a",)
    
    def __init__(self, a):
        Expr.__init__(self)
        ufl_assert(isinstance(a, Expr), "Expecting Expr instance.")
        self._a = a
    
    def operands(self):
        return (self._a, )
    
    def free_indices(self):
        return self._a.free_indices()
    
    def index_dimensions(self):
        return self._a.index_dimensions()
    
    def shape(self):
        return self._a.shape()
    
    def evaluate(self, x, mapping, component, index_values):    
        a = self._a.evaluate(x, mapping, component, index_values)
        return abs(a)
    
    def __str__(self):
        return "| %s |" % str(self._a)
    
    def __repr__(self):
        return "Abs(%r)" % self._a
