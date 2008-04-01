import numpy
from numpy import matrix, ndarray, asarray, dot, atleast_2d, hstack
from scipy.sparse.sputils import isshape
from scipy.sparse import isspmatrix

__all__ = ['LinearOperator', 'aslinearoperator']

class LinearOperator:
    """Common interface for performing matrix vector products

    Many iterative methods (e.g. cg, gmres) do not need to know the
    individual entries of a matrix to solve a linear system A*x=b. 
    Such solvers only require the computation of matrix vector 
    products, A*v where v is a dense vector.  This class serves as
    an abstract interface between iterative solvers and matrix-like
    objects.

    Required Parameters
    -------------------
    shape     : tuple of matrix dimensions (M,N)
    matvec(x) : function that returns A * v

    Optional Parameters
    -------------------
    rmatvec(v) : function that returns A^H * v where A^H represents 
                 the Hermitian (conjugate) transpose of A
    matmat(V)  : function that returns A * V where V is a dense 
                 matrix with dimensions (N,K)
    dtype      : data type of the matrix
                    

    See Also
    --------
    aslinearoperator() : Construct LinearOperators for SciPy classes

    Examples
    --------

    >>> from scipy.sparse.linalg import LinearOperator
    >>> from scipy import *
    >>> def mv(v):
    ...     return array([ 2*v[0], 3*v[1]])
    ... 
    >>> A = LinearOperator( (2,2), matvec=mv )
    >>> A
    <2x2 LinearOperator with unspecified dtype>
    >>> A.matvec( ones(2) )
    array([ 2.,  3.])
    
    """
    def __init__( self, shape, matvec, rmatvec=None, matmat=None, dtype=None ):

        shape = tuple(shape)

        if not isshape(shape):
            raise ValueError('invalid shape')

        self.shape  = shape
        self.matvec = matvec

        if rmatvec is None:
            def rmatvec(v):
                raise NotImplementedError('rmatvec is not defined')
            self.rmatvec = rmatvec
        else:
            self.rmatvec = rmatvec

        if matmat is None:
            # matvec each column of V
            def matmat(V):
                V = asarray(V)
                return hstack( [ matvec(col.reshape(-1,1)) for col in V.T ] )
            self.matmat = matmat
        else:
            self.matmat = matmat

        if dtype is not None:
            self.dtype = numpy.dtype(dtype)

    def __repr__(self):
        M,N = self.shape
        if hasattr(self,'dtype'):
            dt = 'dtype=' + str(self.dtype)
        else:
            dt = 'unspecified dtype'

        return '<%dx%d LinearOperator with %s>' % (M,N,dt)

def aslinearoperator(A):
    """Return A as a LinearOperator

    'A' may be any of the following types
        - ndarray
        - matrix
        - sparse matrix (e.g. csr_matrix, lil_matrix, etc.)
        - LinearOperator
        - An object with .shape and .matvec attributes

    See the LinearOperator documentation for additonal information.

    Examples
    ========
    
    >>> from scipy import matrix
    >>> M = matrix( [[1,2,3],[4,5,6]], dtype='int32' )
    >>> aslinearoperator( M )
    <2x3 LinearOperator with dtype=int32>

    """

    if isinstance(A, LinearOperator):
        return A

    elif isinstance(A, ndarray) or isinstance(A, matrix):
        if len(A.shape) > 2:
            raise ValueError('array must have rank <= 2')

        A = atleast_2d(asarray(A))

        def matvec(v):
            return dot(A, v)
        def rmatvec(v):
            return dot(A.conj().transpose(), v)
        def matmat(V):
            return dot(A, V)
        return LinearOperator( A.shape, matvec, rmatvec=rmatvec, \
                matmat=matmat, dtype=A.dtype )

    elif isspmatrix(A):
        return LinearOperator( A.shape, A.matvec, rmatvec=A.rmatvec, \
                matmat=A.dot, dtype=A.dtype ) 

    else:
        if hasattr(A,'shape') and hasattr(A,'matvec'):
            rmatvec = None
            dtype = None

            if hasattr(A,'rmatvec'):
                rmatvec = A.rmatvec
            if hasattr(A,'dtype'):
                dtype = A.dtype
            return LinearOperator(A.shape, A.matvec, rmatvec=rmatvec, dtype=dtype)

        else:
            raise TypeError('type not understood')


