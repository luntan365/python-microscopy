/*
##################
# gauss_ap.c
#
# Copyright David Baddeley, 2010
# d.baddeley@auckland.ac.nz
#
# This file may NOT be distributed without express permision from David Baddeley
#
##################
 */

#include "Python.h"
#include <complex.h>
#include <math.h>
#include "numpy/arrayobject.h"
#include <stdio.h>

#define MIN(a, b) ((a<b) ? a : b) 
#define MAX(a, b) ((a>b) ? a : b)

#define LITTLEENDIAN


//Really dodgy fast approximation to exponential
static union
{
  double d;
  struct
  {

#ifdef LITTLEENDIAN
    int j, i;
#else
    int i, j;
#endif
  } n;
} eco;

#define EXP_A (1048576/M_LN2) /* use 1512775 for integer version */
#define EXP_C 60801 /* see text for choice of c values */
#define EXP(y) (eco.n.i = EXP_A*(y) + (1072693248 - EXP_C), eco.d)
//end eponential approx

//normalisation factor for 3D Gaussian
#define TDNORM 15.75

static PyObject * genGauss(PyObject *self, PyObject *args, PyObject *keywds) 
{
    double *res = 0;  
    int ix,iy; 
    int size[2];
    
    PyObject *oX =0;
    PyObject *oY=0;
    
    PyArrayObject* Xvals;
    PyArrayObject* Yvals;
    
    PyArrayObject* out;
    
    double *pXvals;
    double *pYvals;
    
    /*parameters*/
    double A = 1;
    double x0 = 0;
    double y0 = 0;
    double sigma = 1;
    double b = 0;
    double b_x = 0;
    double b_y = 0;

    /*End paramters*/

    double ts2;
    double byY;

      
    
    static char *kwlist[] = {"X", "Y", "A","x0", "y0","sigma","b","b_x","b_y", NULL};
    
    if (!PyArg_ParseTupleAndKeywords(args, keywds, "OO|ddddddd", kwlist, 
         &oX, &oY, &A, &x0, &y0, &sigma, &b, &b_x, &b_y))
        return NULL; 

    /* Do the calculations */ 
        
    Xvals = (PyArrayObject *) PyArray_ContiguousFromObject(oX, PyArray_DOUBLE, 0, 1);
    if (Xvals == NULL) 
    {
      PyErr_Format(PyExc_RuntimeError, "Bad X");   
      return NULL;
    }
    
    Yvals = (PyArrayObject *) PyArray_ContiguousFromObject(oY, PyArray_DOUBLE, 0, 1);
    if (Yvals == NULL)
    {
        Py_DECREF(Xvals);
        PyErr_Format(PyExc_RuntimeError, "Bad Y");
        return NULL;
    }
    
    
    
    pXvals = (double*)Xvals->data;
    pYvals = (double*)Yvals->data;
    
    
    size[0] = PyArray_Size((PyObject*)Xvals);
    size[1] = PyArray_Size((PyObject*)Yvals);
        
    out = (PyArrayObject*) PyArray_FromDims(2,size,PyArray_DOUBLE);
    
    //fix strides
    out->strides[0] = sizeof(double);
    out->strides[1] = sizeof(double)*size[0];
    
    res = (double*) out->data;
    
    ts2 = 2*sigma*sigma;
        
    for (iy = 0; iy < size[1]; iy++)
      {            
	byY = b_y*(pYvals[iy]- y0) + b;
	for (ix = 0; ix < size[0]; ix++)
	  {
	    *res = A*exp(-(((pXvals[ix] - x0) * (pXvals[ix] - x0)) + ((pYvals[iy]-y0) * (pYvals[iy]-y0)))/ts2) + b_x*(pXvals[ix]-x0) + byY;
	    //*res = 1.0;
	    res++;
            
	  }
        
      }
    
    
    Py_DECREF(Xvals);
    Py_DECREF(Yvals);
    
    return (PyObject*) out;
}

static PyObject * genGaussInArray(PyObject *self, PyObject *args, PyObject *keywds)
{
    double *res = 0;
    int ix,iy;
    int size[2];

    PyObject *oX =0;
    PyObject *oY=0;
    PyObject *oOut=0;

    PyArrayObject* Xvals;
    PyArrayObject* Yvals;

    //PyArrayObject* out;

    double *pXvals;
    double *pYvals;

    /*parameters*/
    double A = 1;
    double x0 = 0;
    double y0 = 0;
    double sigma = 1;
    double b = 0;
    double b_x = 0;
    double b_y = 0;

    /*End paramters*/

    double ts2;
    double byY;



    static char *kwlist[] = {"out", "X", "Y", "A","x0", "y0","sigma","b","b_x","b_y", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, keywds, "OOO|ddddddd", kwlist,
         &oOut, &oX, &oY, &A, &x0, &y0, &sigma, &b, &b_x, &b_y))
        return NULL;

    /* Do the calculations */

    Xvals = (PyArrayObject *) PyArray_ContiguousFromObject(oX, PyArray_DOUBLE, 0, 1);
    if (Xvals == NULL)
    {
      PyErr_Format(PyExc_RuntimeError, "Bad X");
      return NULL;
    }

    Yvals = (PyArrayObject *) PyArray_ContiguousFromObject(oY, PyArray_DOUBLE, 0, 1);
    if (Yvals == NULL)
    {
        Py_DECREF(Xvals);
        PyErr_Format(PyExc_RuntimeError, "Bad Y");
        return NULL;
    }

/*
    out = (PyArrayObject *) PyArray_ContiguousFromObject(oOut, PyArray_DOUBLE, 2, 2);
    if (out == NULL)
    {
        Py_DECREF(Xvals);
        Py_DECREF(YVals);
        PyErr_Format(PyExc_RuntimeError, "Bad Y");
        return NULL;
    }
*/
    //out = (PyArrayObject *)oOut;
    //fprintf("array size")

    if (!PyArray_ISFORTRAN(oOut) || PyArray_TYPE(oOut) != PyArray_DOUBLE|| PyArray_DIM(oOut,0) != PyArray_DIM(Xvals, 0) || PyArray_DIM(oOut, 1) != PyArray_DIM(Yvals, 0))
    {
        Py_DECREF(Xvals);
        Py_DECREF(Yvals);
        PyErr_Format(PyExc_RuntimeError, "bad output array");
        return NULL;
    }


    pXvals = (double*)Xvals->data;
    pYvals = (double*)Yvals->data;


    size[0] = PyArray_Size((PyObject*)Xvals);
    size[1] = PyArray_Size((PyObject*)Yvals);

    //out = (PyArrayObject*) PyArray_FromDims(2,size,PyArray_DOUBLE);

    //fix strides
    //out->strides[0] = sizeof(double);
    //out->strides[1] = sizeof(double)*size[0];

    res = (double*) PyArray_DATA(oOut);

    ts2 = 2*sigma*sigma;

    for (iy = 0; iy < size[1]; iy++)
      {
	byY = b_y*(pYvals[iy]- y0) + b;
	for (ix = 0; ix < size[0]; ix++)
	  {
	    *res = A*exp(-(((pXvals[ix] - x0) * (pXvals[ix] - x0)) + ((pYvals[iy]-y0) * (pYvals[iy]-y0)))/ts2) + b_x*(pXvals[ix]-x0) + byY;
	    //*res = 1.0;
	    res++;

	  }

      }


    Py_DECREF(Xvals);
    Py_DECREF(Yvals);

    //return oOut;
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject * genSplitGaussInArray(PyObject *self, PyObject *args, PyObject *keywds)
{
    double *res = 0;
    int ix,iy;
    int size[2];

    PyObject *oX =0;
    PyObject *oY=0;

    PyObject *oX2 =0;
    PyObject *oY2=0;

    PyObject *oOut=0;

    PyArrayObject* Xvals;
    PyArrayObject* Yvals;
    PyArrayObject* X2vals;
    PyArrayObject* Y2vals;

    //PyArrayObject* out;

    double *pXvals;
    double *pYvals;

    /*parameters*/
    double A = 1;
    double A2 = 1;
    double x0 = 0;
    double y0 = 0;
    double sigma = 1;
    double b = 0;
    double b_x = 0;
    double b_y = 0;

    /*End paramters*/

    double ts2;
    double byY;



    static char *kwlist[] = {"out", "X", "Y", "X2", "Y2", "A", "A2","x0", "y0","sigma","b","b_x","b_y", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, keywds, "OOOOO|dddddddd", kwlist,
         &oOut, &oX, &oY, &oX2, &oY2, &A, &A2, &x0, &y0, &sigma, &b, &b_x, &b_y))
        return NULL;

    /* Do the calculations */

    Xvals = (PyArrayObject *) PyArray_ContiguousFromObject(oX, PyArray_DOUBLE, 0, 1);
    if (Xvals == NULL)
    {
      PyErr_Format(PyExc_RuntimeError, "Bad X");
      return NULL;
    }

    Yvals = (PyArrayObject *) PyArray_ContiguousFromObject(oY, PyArray_DOUBLE, 0, 1);
    if (Yvals == NULL)
    {
        Py_DECREF(Xvals);
        PyErr_Format(PyExc_RuntimeError, "Bad Y");
        return NULL;
    }

    X2vals = (PyArrayObject *) PyArray_ContiguousFromObject(oX2, PyArray_DOUBLE, 0, 1);
    if (X2vals == NULL)
    {
      Py_DECREF(Xvals);
      Py_DECREF(Yvals);
      PyErr_Format(PyExc_RuntimeError, "Bad X");
      return NULL;
    }

    Y2vals = (PyArrayObject *) PyArray_ContiguousFromObject(oY2, PyArray_DOUBLE, 0, 1);
    if (Y2vals == NULL)
    {
        Py_DECREF(Xvals);
        Py_DECREF(Yvals);
        Py_DECREF(X2vals);
        PyErr_Format(PyExc_RuntimeError, "Bad Y");
        return NULL;
    }


    if (!PyArray_ISFORTRAN(oOut) || PyArray_TYPE(oOut) != PyArray_DOUBLE|| PyArray_DIM(oOut,0) != PyArray_DIM(Xvals, 0) || PyArray_DIM(oOut, 1) != PyArray_DIM(Yvals, 0))
    {
        Py_DECREF(Xvals);
        Py_DECREF(Yvals);
        Py_DECREF(X2vals);
        Py_DECREF(Y2vals);
        PyErr_Format(PyExc_RuntimeError, "bad output array");
        return NULL;
    }


    pXvals = (double*)Xvals->data;
    pYvals = (double*)Yvals->data;


    size[0] = PyArray_Size((PyObject*)Xvals);
    size[1] = PyArray_Size((PyObject*)Yvals);

    //out = (PyArrayObject*) PyArray_FromDims(2,size,PyArray_DOUBLE);

    //fix strides
    //out->strides[0] = sizeof(double);
    //out->strides[1] = sizeof(double)*size[0];

    res = (double*) PyArray_DATA(oOut);

    ts2 = 2*sigma*sigma;

    for (iy = 0; iy < size[1]; iy++)
      {
	byY = b_y*(pYvals[iy]- y0) + b;
	for (ix = 0; ix < size[0]; ix++)
	  {
	    *res = A*exp(-(((pXvals[ix] - x0) * (pXvals[ix] - x0)) + ((pYvals[iy]-y0) * (pYvals[iy]-y0)))/ts2) + b_x*(pXvals[ix]-x0) + byY;
	    //*res = 1.0;
	    res++;

	  }

      }

    pXvals = (double*)X2vals->data;
    pYvals = (double*)Y2vals->data;

    for (iy = 0; iy < size[1]; iy++)
      {
	byY = b_y*(pYvals[iy]- y0) + b;
	for (ix = 0; ix < size[0]; ix++)
	  {
	    *res = A2*exp(-(((pXvals[ix] - x0) * (pXvals[ix] - x0)) + ((pYvals[iy]-y0) * (pYvals[iy]-y0)))/ts2) + b_x*(pXvals[ix]-x0) + byY;
	    //*res = 1.0;
	    res++;

	  }

      }


    Py_DECREF(Xvals);
    Py_DECREF(Yvals);
    Py_DECREF(X2vals);
    Py_DECREF(Y2vals);

    //return oOut;
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject * genSplitGaussInArrayPVec(PyObject *self, PyObject *args, PyObject *keywds)
{
    double *res = 0;
    int ix,iy;
    int size[2];

    PyObject *oX =0;
    PyObject *oY=0;

    PyObject *oX2 =0;
    PyObject *oY2=0;

    PyObject *oOut=0;

    PyObject *oParameters = 0;

    PyArrayObject* Xvals;
    PyArrayObject* Yvals;
    PyArrayObject* X2vals;
    PyArrayObject* Y2vals;

     PyArrayObject* pVals;

    //PyArrayObject* out;

    double *pXvals;
    double *pYvals;
    double *ppVals;

    /*parameters*/
    double A = 1;
    double A2 = 1;
    double x0 = 0;
    double y0 = 0;
    double sigma = 1;
    double b = 0;
    double b_x = 0;
    double b_y = 0;

    /*End paramters*/

    double ts2;
    double byY;

    int nParams=0;



    static char *kwlist[] = {"P", "X", "Y", "X2", "Y2","out", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, keywds, "OOOOOO", kwlist,
         &oParameters, &oX, &oY, &oX2, &oY2, &oOut))
        return NULL;

    /* Do the calculations */

    pVals = (PyArrayObject *) PyArray_ContiguousFromObject(oParameters, PyArray_DOUBLE, 0, 1);
    if (pVals == NULL)
    {
      PyErr_Format(PyExc_RuntimeError, "Bad X");
      return NULL;
    }

    nParams = PyArray_DIM(pVals, 0);
    ppVals = PyArray_DATA(pVals);

    if (nParams >= 1) {A = ppVals[0];
    if (nParams >= 2) {A2 = ppVals[1];
    if (nParams >= 3) {x0 = ppVals[2];
    if (nParams >= 4) {y0 = ppVals[3];
    if (nParams >= 5) {sigma = ppVals[4];
    if (nParams >= 6) {b = ppVals[5];
    if (nParams >= 7) {b_x = ppVals[6];
    if (nParams >= 8) b_y = ppVals[7];
    }}}}}}}


    Xvals = (PyArrayObject *) PyArray_ContiguousFromObject(oX, PyArray_DOUBLE, 0, 1);
    if (Xvals == NULL)
    {
      Py_DECREF(pVals);
      PyErr_Format(PyExc_RuntimeError, "Bad X");
      return NULL;
    }

    Yvals = (PyArrayObject *) PyArray_ContiguousFromObject(oY, PyArray_DOUBLE, 0, 1);
    if (Yvals == NULL)
    {
        Py_DECREF(Xvals);
        Py_DECREF(pVals);
        PyErr_Format(PyExc_RuntimeError, "Bad Y");
        return NULL;
    }

    X2vals = (PyArrayObject *) PyArray_ContiguousFromObject(oX2, PyArray_DOUBLE, 0, 1);
    if (X2vals == NULL)
    {
      Py_DECREF(Xvals);
      Py_DECREF(Yvals);
      Py_DECREF(pVals);
      PyErr_Format(PyExc_RuntimeError, "Bad X");
      return NULL;
    }

    Y2vals = (PyArrayObject *) PyArray_ContiguousFromObject(oY2, PyArray_DOUBLE, 0, 1);
    if (Y2vals == NULL)
    {
        Py_DECREF(Xvals);
        Py_DECREF(Yvals);
        Py_DECREF(X2vals);
        Py_DECREF(pVals);
        PyErr_Format(PyExc_RuntimeError, "Bad Y");
        return NULL;
    }


    if (!PyArray_ISFORTRAN(oOut) || PyArray_TYPE(oOut) != PyArray_DOUBLE|| PyArray_DIM(oOut,0) != PyArray_DIM(Xvals, 0) || PyArray_DIM(oOut, 1) != PyArray_DIM(Yvals, 0))
    {
        Py_DECREF(Xvals);
        Py_DECREF(Yvals);
        Py_DECREF(X2vals);
        Py_DECREF(Y2vals);
        Py_DECREF(pVals);
        PyErr_Format(PyExc_RuntimeError, "bad output array");
        return NULL;
    }


    pXvals = (double*)Xvals->data;
    pYvals = (double*)Yvals->data;


    size[0] = PyArray_Size((PyObject*)Xvals);
    size[1] = PyArray_Size((PyObject*)Yvals);

    //out = (PyArrayObject*) PyArray_FromDims(2,size,PyArray_DOUBLE);

    //fix strides
    //out->strides[0] = sizeof(double);
    //out->strides[1] = sizeof(double)*size[0];

    res = (double*) PyArray_DATA(oOut);

    ts2 = 2*sigma*sigma;

    for (iy = 0; iy < size[1]; iy++)
      {
	byY = b_y*(pYvals[iy]- y0) + b;
	for (ix = 0; ix < size[0]; ix++)
	  {
	    *res = A*exp(-(((pXvals[ix] - x0) * (pXvals[ix] - x0)) + ((pYvals[iy]-y0) * (pYvals[iy]-y0)))/ts2) + b_x*(pXvals[ix]-x0) + byY;
	    //*res = 1.0;
	    res++;

	  }

      }

    pXvals = (double*)X2vals->data;
    pYvals = (double*)Y2vals->data;

    for (iy = 0; iy < size[1]; iy++)
      {
	byY = b_y*(pYvals[iy]- y0) + b;
	for (ix = 0; ix < size[0]; ix++)
	  {
	    *res = A2*exp(-(((pXvals[ix] - x0) * (pXvals[ix] - x0)) + ((pYvals[iy]-y0) * (pYvals[iy]-y0)))/ts2) + b_x*(pXvals[ix]-x0) + byY;
	    //*res = 1.0;
	    res++;

	  }

      }


    Py_DECREF(Xvals);
    Py_DECREF(Yvals);
    Py_DECREF(X2vals);
    Py_DECREF(Y2vals);
    Py_DECREF(pVals);

    Py_INCREF(oOut);
    return oOut;
    //Py_INCREF(Py_None);
    //return Py_None;
}

static PyObject *splitGaussArrayPVecWeightedMisfit(PyObject *self, PyObject *args, PyObject *keywds)
{
    double *res = 0;
    double *data = 0;
    double *weights = 0;
    int ix,iy;
    int size[2];
    int dims[2];

    PyObject *oX =0;
    PyObject *oY=0;

    PyObject *oX2 =0;
    PyObject *oY2=0;

    PyObject *oOut=0;
    PyObject *oData=0;
    PyObject *oWeights=0;

    PyObject *oParameters = 0;

    PyArrayObject* Xvals;
    PyArrayObject* Yvals;
    PyArrayObject* X2vals;
    PyArrayObject* Y2vals;

     PyArrayObject* pVals;

    //PyArrayObject* out;

    double *pXvals;
    double *pYvals;
    double *ppVals;

    /*parameters*/
    double A = 1;
    double A2 = 1;
    double x0 = 0;
    double y0 = 0;
    double sigma = 1;
    double b = 0;
    double b1 = 0;
    double b_x = 0;
    double b_y = 0;

    /*End paramters*/

    double ts2;
    double byY;

    int nParams=0;



    static char *kwlist[] = {"P", "Data", "Weights","X", "Y", "X2", "Y2", "out", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, keywds, "OOOOOOOO", kwlist,
         &oParameters, &oData, &oWeights, &oX, &oY, &oX2, &oY2, &oOut))
        return NULL;

    /* Do the calculations */

    pVals = (PyArrayObject *) PyArray_ContiguousFromObject(oParameters, PyArray_DOUBLE, 0, 1);
    if (pVals == NULL)
    {
      PyErr_Format(PyExc_RuntimeError, "Bad X");
      return NULL;
    }

    nParams = PyArray_DIM(pVals, 0);
    ppVals = PyArray_DATA(pVals);

    if (nParams >= 1) {A = ppVals[0];
    if (nParams >= 2) {A2 = ppVals[1];
    if (nParams >= 3) {x0 = ppVals[2];
    if (nParams >= 4) {y0 = ppVals[3];
    if (nParams >= 5) {sigma = ppVals[4];
    if (nParams >= 6) {b = ppVals[5];
    if (nParams >= 7) {b1 = ppVals[6];
    if (nParams >= 8) {b_x = ppVals[7];
    if (nParams >= 9) b_y = ppVals[8];
    }}}}}}}}


    Xvals = (PyArrayObject *) PyArray_ContiguousFromObject(oX, PyArray_DOUBLE, 0, 1);
    if (Xvals == NULL)
    {
      Py_DECREF(pVals);
      PyErr_Format(PyExc_RuntimeError, "Bad X");
      return NULL;
    }

    Yvals = (PyArrayObject *) PyArray_ContiguousFromObject(oY, PyArray_DOUBLE, 0, 1);
    if (Yvals == NULL)
    {
        Py_DECREF(Xvals);
        Py_DECREF(pVals);
        PyErr_Format(PyExc_RuntimeError, "Bad Y");
        return NULL;
    }

    X2vals = (PyArrayObject *) PyArray_ContiguousFromObject(oX2, PyArray_DOUBLE, 0, 1);
    if (X2vals == NULL)
    {
      Py_DECREF(Xvals);
      Py_DECREF(Yvals);
      Py_DECREF(pVals);
      PyErr_Format(PyExc_RuntimeError, "Bad X");
      return NULL;
    }

    Y2vals = (PyArrayObject *) PyArray_ContiguousFromObject(oY2, PyArray_DOUBLE, 0, 1);
    if (Y2vals == NULL)
    {
        Py_DECREF(Xvals);
        Py_DECREF(Yvals);
        Py_DECREF(X2vals);
        Py_DECREF(pVals);
        PyErr_Format(PyExc_RuntimeError, "Bad Y");
        return NULL;
    }

    if (!PyArray_ISFORTRAN(oData) || PyArray_TYPE(oData) != PyArray_DOUBLE|| PyArray_DIM(oData,0) != PyArray_DIM(Xvals, 0) || PyArray_DIM(oData, 1) != PyArray_DIM(Yvals, 0))
    {
        Py_DECREF(Xvals);
        Py_DECREF(Yvals);
        Py_DECREF(X2vals);
        Py_DECREF(Y2vals);
        Py_DECREF(pVals);
        PyErr_Format(PyExc_RuntimeError, "bad data array");
        return NULL;
    }

    if (!PyArray_ISFORTRAN(oWeights) || PyArray_TYPE(oWeights) != PyArray_DOUBLE|| PyArray_DIM(oWeights,0) != PyArray_DIM(Xvals, 0) || PyArray_DIM(oWeights, 1) != PyArray_DIM(Yvals, 0))
    {
        Py_DECREF(Xvals);
        Py_DECREF(Yvals);
        Py_DECREF(X2vals);
        Py_DECREF(Y2vals);
        Py_DECREF(pVals);
        PyErr_Format(PyExc_RuntimeError, "bad weights array");
        return NULL;
    }


/*
    dims[0] = PyArray_SIZE(oData);
    printf("trying to allocate arrya of size: %d\n", dims[0]);

    oOut = PyArray_SimpleNew(1, dims, PyArray_DOUBLE);
    
    if (oOut == NULL)
    {
        Py_DECREF(Xvals);
        Py_DECREF(Yvals);
        Py_DECREF(X2vals);
        Py_DECREF(Y2vals);
        Py_DECREF(pVals);
        PyErr_Format(PyExc_RuntimeError, "error allocating output array");
        return NULL;
    }
*/



    if (PyArray_TYPE(oOut) != PyArray_DOUBLE|| PyArray_SIZE(oOut) != PyArray_SIZE(oData))
    {
        Py_DECREF(Xvals);
        Py_DECREF(Yvals);
        Py_DECREF(X2vals);
        Py_DECREF(Y2vals);
        Py_DECREF(pVals);
        PyErr_Format(PyExc_RuntimeError, "bad output array");
        return NULL;
    }


    pXvals = (double*)Xvals->data;
    pYvals = (double*)Yvals->data;


    size[0] = PyArray_Size((PyObject*)Xvals);
    size[1] = PyArray_Size((PyObject*)Yvals);

    //out = (PyArrayObject*) PyArray_FromDims(2,size,PyArray_DOUBLE);

    //fix strides
    //out->strides[0] = sizeof(double);
    //out->strides[1] = sizeof(double)*size[0];

    res = (double*) PyArray_DATA(oOut);
    data = (double*) PyArray_DATA(oData);
    weights = (double*) PyArray_DATA(oWeights);

    ts2 = 2*sigma*sigma;

    for (iy = 0; iy < size[1]; iy++)
      {
	byY = b_y*(pYvals[iy]- y0) + b;
	for (ix = 0; ix < size[0]; ix++)
	  {
	    *res = (*weights)*(*data - A*exp(-(((pXvals[ix] - x0) * (pXvals[ix] - x0)) + ((pYvals[iy]-y0) * (pYvals[iy]-y0)))/ts2) + b_x*(pXvals[ix]-x0) + byY);
	    //*res = 1.0;
	    res++;
            data++;
            weights++;
            
	  }

      }

    pXvals = (double*)X2vals->data;
    pYvals = (double*)Y2vals->data;

    for (iy = 0; iy < size[1]; iy++)
      {
	byY = b_y*(pYvals[iy]- y0) + b1;
	for (ix = 0; ix < size[0]; ix++)
	  {
	    *res = (*weights)*(*data -A2*exp(-(((pXvals[ix] - x0) * (pXvals[ix] - x0)) + ((pYvals[iy]-y0) * (pYvals[iy]-y0)))/ts2) + b_x*(pXvals[ix]-x0) + byY);
	    //*res = 1.0;
	    res++;
            data++;
            weights++;
	  }

      }


    Py_DECREF(Xvals);
    Py_DECREF(Yvals);
    Py_DECREF(X2vals);
    Py_DECREF(Y2vals);
    Py_DECREF(pVals);

    Py_INCREF(oOut);
    return oOut;
    //Py_INCREF(Py_None);
    //return Py_None;
}

static PyObject * genGauss3D(PyObject *self, PyObject *args, PyObject *keywds)
{
    double *res = 0;
    int ix,iy,iz;
    int size[3];

    PyObject *oX =0;
    PyObject *oY=0;
    PyObject *oZ=0;

    PyArrayObject* Xvals;
    PyArrayObject* Yvals;
    PyArrayObject* Zvals;

    PyArrayObject* out;

    double *pXvals;
    double *pYvals;
    double *pZvals;

    /*parameters*/
    double A = 1;
    double x0 = 0;
    double y0 = 0;
    double z0 = 0;
    double sigma = 1;
    double sigma_z = 1;
    double b = 0;
    //double b_x = 0;
    //double b_y = 0;

    /*End paramters*/

    double ts2, tsz2;
    //double byY;



    static char *kwlist[] = {"X", "Y", "Z", "A","x0", "y0", "z0","sigma", "sigma_z", "b", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, keywds, "OOO|ddddddd", kwlist,
         &oX, &oY, &oZ, &A, &x0, &y0, &z0, &sigma, &sigma_z, &b))
        return NULL;

    /* Do the calculations */

    Xvals = (PyArrayObject *) PyArray_ContiguousFromObject(oX, PyArray_DOUBLE, 0, 1);
    if (Xvals == NULL)
    {
      PyErr_Format(PyExc_RuntimeError, "Bad X");
      return NULL;
    }

    Yvals = (PyArrayObject *) PyArray_ContiguousFromObject(oY, PyArray_DOUBLE, 0, 1);
    if (Yvals == NULL)
    {
        Py_DECREF(Xvals);
        PyErr_Format(PyExc_RuntimeError, "Bad Y");
        return NULL;
    }

    Zvals = (PyArrayObject *) PyArray_ContiguousFromObject(oZ, PyArray_DOUBLE, 0, 1);
    if (Zvals == NULL)
    {
        Py_DECREF(Xvals);
        Py_DECREF(Yvals);
        PyErr_Format(PyExc_RuntimeError, "Bad Z");
        return NULL;
    }



    pXvals = (double*)Xvals->data;
    pYvals = (double*)Yvals->data;
    pZvals = (double*)Zvals->data;


    size[0] = PyArray_Size((PyObject*)Xvals);
    size[1] = PyArray_Size((PyObject*)Yvals);
    size[2] = PyArray_Size((PyObject*)Zvals);

    out = (PyArrayObject*) PyArray_FromDims(3,size,PyArray_DOUBLE);

    //fix strides
    out->strides[0] = sizeof(double);
    out->strides[1] = sizeof(double)*size[0];
    out->strides[2] = sizeof(double)*size[0]*size[1];

    res = (double*) out->data;

    ts2 = 2*sigma*sigma;
    tsz2 = 2*sigma_z*sigma_z;

    A = A/(sigma*sigma*sigma_z*TDNORM);

    for (iz = 0; iz < size[2]; iz ++)
    {
        for (iy = 0; iy < size[1]; iy++)
          {
            //byY = b_y*(pYvals[iy]- y0) + b;
            for (ix = 0; ix < size[0]; ix++)
              {
                *res = A*exp(-(((pXvals[ix] - x0) * (pXvals[ix] - x0)) + ((pYvals[iy]-y0) * (pYvals[iy]-y0)))/ts2 - (((pZvals[iz] - z0) * (pZvals[iz] - z0)) )/tsz2) + b;
                //*res = 1.0;
                res++;

              }

          }
    }


    Py_DECREF(Xvals);
    Py_DECREF(Yvals);
    Py_DECREF(Zvals);

    return (PyObject*) out;
}


//same as above but using dodgy exponential
static PyObject * genGaussF(PyObject *self, PyObject *args, PyObject *keywds) 
{
    double *res = 0;  
    int ix,iy; 
    int size[2];
    
    PyObject *oX =0;
    PyObject *oY=0;
    
    PyArrayObject* Xvals;
    PyArrayObject* Yvals;
    
    PyArrayObject* out;
    
    double *pXvals;
    double *pYvals;
    
    /*parameters*/
    double A = 1;
    double x0 = 0;
    double y0 = 0;
    double sigma = 1;
    double b = 0;
    double b_x = 0;
    double b_y = 0;

    /*End paramters*/

    double ts2;
    double byY;

    //double g_;

      
    
    static char *kwlist[] = {"X", "Y", "A","x0", "y0","sigma","b","b_x","b_y", NULL};
    
    if (!PyArg_ParseTupleAndKeywords(args, keywds, "OO|ddddddd", kwlist, 
         &oX, &oY, &A, &x0, &y0, &sigma, &b, &b_x, &b_y))
        return NULL; 

    /* Do the calculations */ 
        
    Xvals = (PyArrayObject *) PyArray_ContiguousFromObject(oX, PyArray_DOUBLE, 0, 1);
    if (Xvals == NULL) 
    {
      PyErr_Format(PyExc_RuntimeError, "Bad X");   
      return NULL;
    }
    
    Yvals = (PyArrayObject *) PyArray_ContiguousFromObject(oY, PyArray_DOUBLE, 0, 1);
    if (Yvals == NULL)
    {
        Py_DECREF(Xvals);
        PyErr_Format(PyExc_RuntimeError, "Bad Y");
        return NULL;
    }
    
    
    
    pXvals = (double*)Xvals->data;
    pYvals = (double*)Yvals->data;
    
    
    size[0] = PyArray_Size((PyObject*)Xvals);
    size[1] = PyArray_Size((PyObject*)Yvals);
        
    out = (PyArrayObject*) PyArray_FromDims(2,size,PyArray_DOUBLE);
    
    //fix strides
    out->strides[0] = sizeof(double);
    out->strides[1] = sizeof(double)*size[0];
    
    res = (double*) out->data;
    
    ts2 = 2*sigma*sigma;
        
    for (iy = 0; iy < size[1]; iy++)
      {            
	byY = b_y*(pYvals[iy]-y0) + b;
	for (ix = 0; ix < size[0]; ix++)
	  {
	    *res = A*EXP(-(((pXvals[ix] - x0) * (pXvals[ix] - x0)) + ((pYvals[iy]-y0) * (pYvals[iy]-y0)))/ts2) + b_x*(pXvals[ix]-x0) + byY;
	    //*res = 1.0;
	    res++;
            
	  }
        
      }
    
    
    Py_DECREF(Xvals);
    Py_DECREF(Yvals);
    
    return (PyObject*) out;
}





//generate jacobian
static PyObject * genGaussFJac(PyObject *self, PyObject *args, PyObject *keywds) 
{
    double *res = 0;  
    int ix,iy; 
    int size[3];
    
    PyObject *oX =0;
    PyObject *oY=0;
    
    PyArrayObject* Xvals;
    PyArrayObject* Yvals;
    
    PyArrayObject* out;
    
    double *pXvals;
    double *pYvals;
    
    /*parameters*/
    double A = 1;
    double x0 = 0;
    double y0 = 0;
    double sigma = 1;
    double b = 0;
    double b_x = 0;
    double b_y = 0;

    /*End paramters*/

    double ts2;
    //double byY;
    double A_s2;
    double g_;

      
    
    static char *kwlist[] = {"X", "Y", "A","x0", "y0","sigma","b","b_x","b_y", NULL};
    
    if (!PyArg_ParseTupleAndKeywords(args, keywds, "OO|ddddddd", kwlist, 
         &oX, &oY, &A, &x0, &y0, &sigma, &b, &b_x, &b_y))
        return NULL; 

    /* Do the calculations */ 
        
    Xvals = (PyArrayObject *) PyArray_ContiguousFromObject(oX, PyArray_DOUBLE, 0, 1);
    if (Xvals == NULL) 
    {
      PyErr_Format(PyExc_RuntimeError, "Bad X");   
      return NULL;
    }
    
    Yvals = (PyArrayObject *) PyArray_ContiguousFromObject(oY, PyArray_DOUBLE, 0, 1);
    if (Yvals == NULL)
    {
        Py_DECREF(Xvals);
        PyErr_Format(PyExc_RuntimeError, "Bad Y");
        return NULL;
    }
    
    
    
    pXvals = (double*)Xvals->data;
    pYvals = (double*)Yvals->data;
    
    size[1] = PyArray_Size((PyObject*)Xvals);
    size[2] = PyArray_Size((PyObject*)Yvals);
    size[0] = 7;
        
    out = (PyArrayObject*) PyArray_FromDims(3,size,PyArray_DOUBLE);
    
    //fix strides
    out->strides[0] = sizeof(double);
    out->strides[1] = sizeof(double)*size[0];
    out->strides[2] = sizeof(double)*size[0]*size[1];
    
    res = (double*) out->data;
    
    ts2 = 1/(2*sigma*sigma);
    A_s2 = A/(sigma*sigma);
        
    for (ix = 0; ix < size[1]; ix++)
      {            
	//byY = b_y*pYvals[iy] + b;
	for (iy = 0; iy < size[2]; iy++)
	  {
	    g_ = EXP(-(((pXvals[ix] - x0) * (pXvals[ix] - x0)) + ((pYvals[iy]-y0) * (pYvals[iy]-y0)))*ts2);
	    *res = g_; // d/dA
	    res++;
	    g_ *= A_s2;
	    *res = (pXvals[ix] - x0)*g_; // d/dx0
	    res++;
	    *res = (pYvals[iy] - y0)*g_; // d/dx0
	    res++;
	    *res = (((pXvals[ix] - x0) * (pXvals[ix] - x0)) + ((pYvals[iy]-y0) * (pYvals[iy]-y0)))*g_/sigma; // d/dsigma
	    res++;
	    *res = 1.0;
	    res++;
	    *res = pXvals[ix];
	    res++;
	    *res = pYvals[iy];
	    //*res = 1.0;
	    res++;
            
	  }
        
      }
    
    
    Py_DECREF(Xvals);
    Py_DECREF(Yvals);
    
    return (PyObject*) out;
}


static PyObject * genGaussJac(PyObject *self, PyObject *args, PyObject *keywds) 
{
    double *res = 0;  
    int ix,iy; 
    int size[3];
    
    PyObject *oX =0;
    PyObject *oY=0;
    
    PyArrayObject* Xvals;
    PyArrayObject* Yvals;
    
    PyArrayObject* out;
    
    double *pXvals;
    double *pYvals;
    
    /*parameters*/
    double A = 1;
    double x0 = 0;
    double y0 = 0;
    double sigma = 1;
    double b = 0;
    double b_x = 0;
    double b_y = 0;

    /*End paramters*/

    double ts2;
    //double byY;
    double A_s2;
    double g_;

      
    
    static char *kwlist[] = {"X", "Y", "A","x0", "y0","sigma","b","b_x","b_y", NULL};
    
    if (!PyArg_ParseTupleAndKeywords(args, keywds, "OO|ddddddd", kwlist, 
         &oX, &oY, &A, &x0, &y0, &sigma, &b, &b_x, &b_y))
        return NULL; 

    /* Do the calculations */ 
        
    Xvals = (PyArrayObject *) PyArray_ContiguousFromObject(oX, PyArray_DOUBLE, 0, 1);
    if (Xvals == NULL) 
    {
      PyErr_Format(PyExc_RuntimeError, "Bad X");   
      return NULL;
    }
    
    Yvals = (PyArrayObject *) PyArray_ContiguousFromObject(oY, PyArray_DOUBLE, 0, 1);
    if (Yvals == NULL)
    {
        Py_DECREF(Xvals);
        PyErr_Format(PyExc_RuntimeError, "Bad Y");
        return NULL;
    }
    
    
    
    pXvals = (double*)Xvals->data;
    pYvals = (double*)Yvals->data;
    
    size[1] = PyArray_Size((PyObject*)Xvals);
    size[2] = PyArray_Size((PyObject*)Yvals);
    size[0] = 7;
        
    out = (PyArrayObject*) PyArray_FromDims(3,size,PyArray_DOUBLE);
    
    //fix strides
    out->strides[0] = sizeof(double);
    out->strides[1] = sizeof(double)*size[0];
    out->strides[2] = sizeof(double)*size[0]*size[1];
    
    res = (double*) out->data;
    
    ts2 = 1/(2*sigma*sigma);
    A_s2 = A/(sigma*sigma);
        
    for (ix = 0; ix < size[1]; ix++)
      {            
	//byY = b_y*pYvals[iy] + b;
	for (iy = 0; iy < size[2]; iy++)
	  {
	    g_ = exp(-(((pXvals[ix] - x0) * (pXvals[ix] - x0)) + ((pYvals[iy]-y0) * (pYvals[iy]-y0)))*ts2);
	    *res = g_; // d/dA
	    res++;
	    g_ *= A_s2;
	    *res = (pXvals[ix] - x0)*g_; // d/dx0
	    res++;
	    *res = (pYvals[iy] - y0)*g_; // d/dx0
	    res++;
	    *res = (((pXvals[ix] - x0) * (pXvals[ix] - x0)) + ((pYvals[iy]-y0) * (pYvals[iy]-y0)))*g_/sigma; // d/dsigma
	    res++;
	    *res = 1.0;
	    res++;
	    *res = pXvals[ix];
	    res++;
	    *res = pYvals[iy];
	    //*res = 1.0;
	    res++;
            
	  }
        
      }
    
    
    Py_DECREF(Xvals);
    Py_DECREF(Yvals);
    
    return (PyObject*) out;
}

static PyObject * genGaussJacW(PyObject *self, PyObject *args, PyObject *keywds) 
{
    double *res = 0;  
    int ix,iy; 
    int size[3];
    
    PyObject *oX =0;
    PyObject *oY=0;
    PyObject *oW=0;
    
    PyArrayObject* Xvals;
    PyArrayObject* Yvals;
    PyArrayObject* weights;
    
    PyArrayObject* out;
    
    double *pXvals;
    double *pYvals;
    double *pWeights;
    
    /*parameters*/
    double A = 1;
    double x0 = 0;
    double y0 = 0;
    double sigma = 1;
    double b = 0;
    double b_x = 0;
    double b_y = 0;

    /*End paramters*/

    double ts2;
    //double byY;
    double A_s2;
    double g_;
    double w;
      
    
    static char *kwlist[] = {"X", "Y", "W", "A","x0", "y0","sigma","b","b_x","b_y", NULL};
    
    if (!PyArg_ParseTupleAndKeywords(args, keywds, "OOO|ddddddd", kwlist, 
				     &oX, &oY, &oW, &A, &x0, &y0, &sigma, &b, &b_x, &b_y))
        return NULL; 

    /* Do the calculations */ 
        
    Xvals = (PyArrayObject *) PyArray_ContiguousFromObject(oX, PyArray_DOUBLE, 0, 1);
    if (Xvals == NULL) 
    {
      PyErr_Format(PyExc_RuntimeError, "Bad X");   
      return NULL;
    }
    
    Yvals = (PyArrayObject *) PyArray_ContiguousFromObject(oY, PyArray_DOUBLE, 0, 1);
    if (Yvals == NULL)
    {
        Py_DECREF(Xvals);
        PyErr_Format(PyExc_RuntimeError, "Bad Y");
        return NULL;
    }
    
    weights = (PyArrayObject *) PyArray_ContiguousFromObject(oW, PyArray_DOUBLE, 0, 1);
    if (weights == NULL)
    {
        Py_DECREF(Xvals);
	Py_DECREF(Yvals);
        PyErr_Format(PyExc_RuntimeError, "Bad weights");
        return NULL;
    }
    
    pXvals = (double*)Xvals->data;
    pYvals = (double*)Yvals->data;
    pWeights = (double*)weights->data;
    
    size[1] = PyArray_Size((PyObject*)Xvals);
    size[2] = PyArray_Size((PyObject*)Yvals);
    size[0] = 7;

    if (!PyArray_Size((PyObject*)weights) == size[1]*size[2])
    {
        Py_DECREF(Xvals);
	Py_DECREF(Yvals);
	Py_DECREF(weights);
        PyErr_Format(PyExc_RuntimeError, "size of weights does not match that of data");
        return NULL;
    }
        
        
    out = (PyArrayObject*) PyArray_FromDims(3,size,PyArray_DOUBLE);
    
    //fix strides
    out->strides[0] = sizeof(double);
    out->strides[1] = sizeof(double)*size[0];
    out->strides[2] = sizeof(double)*size[0]*size[1];
    
    res = (double*) out->data;
    
    ts2 = 1/(2*sigma*sigma);
    A_s2 = A/(sigma*sigma);
        
    for (ix = 0; ix < size[1]; ix++)
      {            
	//byY = b_y*pYvals[iy] + b;
	for (iy = 0; iy < size[2]; iy++)
	  {
	    w = *pWeights;
	    g_ = w*exp(-(((pXvals[ix] - x0) * (pXvals[ix] - x0)) + ((pYvals[iy]-y0) * (pYvals[iy]-y0)))*ts2);
	    *res = g_; // d/dA
	    res++;
	    g_ *= A_s2;
	    *res = (pXvals[ix] - x0)*g_; // d/dx0
	    res++;
	    *res = (pYvals[iy] - y0)*g_; // d/dx0
	    res++;
	    *res = (((pXvals[ix] - x0) * (pXvals[ix] - x0)) + ((pYvals[iy]-y0) * (pYvals[iy]-y0)))*g_/sigma; // d/dsigma
	    res++;
	    *res = w;
	    res++;
	    *res = w*pXvals[ix];
	    res++;
	    *res = w*pYvals[iy];
	    //*res = 1.0;
	    res++;

	    pWeights++;
	  }
        
      }
    
    
    Py_DECREF(Xvals);
    Py_DECREF(Yvals);
    Py_DECREF(weights);
    
    return (PyObject*) out;
}

//Double Gaussian
static PyObject * genGaussA(PyObject *self, PyObject *args, PyObject *keywds) 
{
    double *res = 0;  
    int ix,iy; 
    int size[2];
    
    PyObject *oX =0;
    PyObject *oY=0;
    
    PyArrayObject* Xvals;
    PyArrayObject* Yvals;
    
    PyArrayObject* out;
    
    double *pXvals;
    double *pYvals;
    
    /*parameters*/
    double A = 1;
    double x0 = 0;
    double y0 = 0;
    double sigma_x = 1;
    double sigma_y = 1;
    double b = 0;
    double b_x = 0;
    double b_y = 0;

    /*End paramters*/

    double tsx2;
    double tsy2;
    double byY;

      
    
    static char *kwlist[] = {"X", "Y", "A","x0", "y0","sigma_x", "sigma_y","b","b_x","b_y", NULL};
    
    if (!PyArg_ParseTupleAndKeywords(args, keywds, "OO|dddddddd", kwlist, 
         &oX, &oY, &A, &x0, &y0, &sigma_x,  &sigma_y,&b, &b_x, &b_y))
        return NULL; 

    /* Do the calculations */ 
        
    Xvals = (PyArrayObject *) PyArray_ContiguousFromObject(oX, PyArray_DOUBLE, 0, 1);
    if (Xvals == NULL) 
    {
      PyErr_Format(PyExc_RuntimeError, "Bad X");   
      return NULL;
    }
    
    Yvals = (PyArrayObject *) PyArray_ContiguousFromObject(oY, PyArray_DOUBLE, 0, 1);
    if (Yvals == NULL)
    {
        Py_DECREF(Xvals);
        PyErr_Format(PyExc_RuntimeError, "Bad Y");
        return NULL;
    }
    
    
    
    pXvals = (double*)Xvals->data;
    pYvals = (double*)Yvals->data;
    
    
    size[0] = PyArray_Size((PyObject*)Xvals);
    size[1] = PyArray_Size((PyObject*)Yvals);
        
    out = (PyArrayObject*) PyArray_FromDims(2,size,PyArray_DOUBLE);
    
    //fix strides
    out->strides[0] = sizeof(double);
    out->strides[1] = sizeof(double)*size[0];
    
    res = (double*) out->data;
    
    tsx2 = 2*sigma_x*sigma_x;
    tsy2 = 2*sigma_y*sigma_y;
        
    for (iy = 0; iy < size[1]; iy++)
      {            
	byY = b_y*pYvals[iy] + b;
	for (ix = 0; ix < size[0]; ix++)
	  {
	    *res = A*exp(-(((pXvals[ix] - x0) * (pXvals[ix] - x0))/tsx2 + ((pYvals[iy]-y0) * (pYvals[iy]-y0))/tsy2)) + b_x*pXvals[ix] + byY;
	    //*res = 1.0;
	    res++;
            
	  }
        
      }
    
    
    Py_DECREF(Xvals);
    Py_DECREF(Yvals);
    
    return (PyObject*) out;
}


//same as above but using dodgy exponential
static PyObject * genGaussAF(PyObject *self, PyObject *args, PyObject *keywds) 
{
    double *res = 0;  
    int ix,iy; 
    int size[2];
    
    PyObject *oX =0;
    PyObject *oY=0;
    
    PyArrayObject* Xvals;
    PyArrayObject* Yvals;
    
    PyArrayObject* out;
    
    double *pXvals;
    double *pYvals;
    
    /*parameters*/
    double A = 1;
    double x0 = 0;
    double y0 = 0;
    double sigma_x = 1;
    double sigma_y = 1;
    double b = 0;
    double b_x = 0;
    double b_y = 0;

    /*End paramters*/

    double tsx2;
    double tsy2;
    double byY;

      
    
    static char *kwlist[] = {"X", "Y", "A","x0", "y0","sigma_x", "sigma_y","b","b_x","b_y", NULL};
    
    if (!PyArg_ParseTupleAndKeywords(args, keywds, "OO|dddddddd", kwlist, 
         &oX, &oY, &A, &x0, &y0, &sigma_x,  &sigma_y,&b, &b_x, &b_y))
        return NULL; 

    /* Do the calculations */ 
        
    Xvals = (PyArrayObject *) PyArray_ContiguousFromObject(oX, PyArray_DOUBLE, 0, 1);
    if (Xvals == NULL) 
    {
      PyErr_Format(PyExc_RuntimeError, "Bad X");   
      return NULL;
    }
    
    Yvals = (PyArrayObject *) PyArray_ContiguousFromObject(oY, PyArray_DOUBLE, 0, 1);
    if (Yvals == NULL)
    {
        Py_DECREF(Xvals);
        PyErr_Format(PyExc_RuntimeError, "Bad Y");
        return NULL;
    }
    
    
    
    pXvals = (double*)Xvals->data;
    pYvals = (double*)Yvals->data;
    
    
    size[0] = PyArray_Size((PyObject*)Xvals);
    size[1] = PyArray_Size((PyObject*)Yvals);
        
    out = (PyArrayObject*) PyArray_FromDims(2,size,PyArray_DOUBLE);
    
    //fix strides
    out->strides[0] = sizeof(double);
    out->strides[1] = sizeof(double)*size[0];
    
    res = (double*) out->data;
    
    tsx2 = 2*sigma_x*sigma_x;
    tsy2 = 2*sigma_y*sigma_y;
    
        
    for (iy = 0; iy < size[1]; iy++)
      {            
	byY = b_y*(pYvals[iy] - y0) + b;
	for (ix = 0; ix < size[0]; ix++)
	  {
	    *res = A*EXP(-(((pXvals[ix] - x0) * (pXvals[ix] - x0))/tsx2 + ((pYvals[iy]-y0) * (pYvals[iy]-y0))/tsy2)) + b_x*(pXvals[ix] - x0) + byY;
	    //*res = 1.0;
	    res++;
            
	  }
        
      }
    
    
    Py_DECREF(Xvals);
    Py_DECREF(Yvals);
    
    return (PyObject*) out;
}

static PyMethodDef gauss_appMethods[] = {
    {"genGauss",  genGauss, METH_VARARGS | METH_KEYWORDS,
    "Generate a (fast) Gaussian.\n. Arguments are: 'X', 'Y', 'A'=1,'x0'=0, 'y0'=0,sigma=0,b=0,b_x=0,b_y=0"},
    {"genGaussJac",  genGaussJac, METH_VARARGS | METH_KEYWORDS,
    "Generate jacobian for Gaussian.\n. Arguments are: 'X', 'Y', 'A'=1,'x0'=0, 'y0'=0,sigma=0,b=0,b_x=0,b_y=0"},
    {"genGaussJacW",  genGaussJacW, METH_VARARGS | METH_KEYWORDS,
    "Generate jacobian for a weighted Gaussian.\n. Arguments are: 'X', 'Y', 'W','A'=1,'x0'=0, 'y0'=0,sigma=0,b=0,b_x=0,b_y=0"},
    /*{"genGaussF",  genGaussF, METH_VARARGS | METH_KEYWORDS,
    "Generate a (fast) Gaussian using dodgy exponential approx.\n. Arguments are: 'X', 'Y', 'A'=1,'x0'=0, 'y0'=0,sigma=0,b=0,b_x=0,b_y=0"},
    {"genGaussFJac",  genGaussFJac, METH_VARARGS | METH_KEYWORDS,
    "Generate jacobian for Gaussian using dodgy exponential approx.\n. Arguments are: 'X', 'Y', 'A'=1,'x0'=0, 'y0'=0,sigma=0,b=0,b_x=0,b_y=0"},*/
    {"genGaussA",  genGaussA, METH_VARARGS | METH_KEYWORDS,
    "Generate a (fast) astigmatic Gaussian.\n. Arguments are: 'X', 'Y', 'A'=1,'x0'=0, 'y0'=0,sigma_x=1, sigma_y = 1,b=0,b_x=0,b_y=0"},
    /*{"genGaussAF",  genGaussAF, METH_VARARGS | METH_KEYWORDS,
      "Generate a (fast) astigmatic Gaussian using dodgy exponential approx.\n. Arguments are: 'X', 'Y', 'A'=1,'x0'=0, 'y0'=0,'sigma_x'=1, 'sigma_y'=1,b=0,b_x=0,b_y=0"},*/
    {"genGauss3D",  genGauss3D, METH_VARARGS | METH_KEYWORDS,
    "Generate a (fast) 3D Gaussian.\n. Arguments are: 'X', 'Y', 'Z', 'A'=1,'x0'=0, 'y0'=0, 'z0'=0,sigma=0, sigma_z=1, b=0"},
    {"genGaussInArray",  genGaussInArray, METH_VARARGS | METH_KEYWORDS,
    "Generate a Gaussian in pre-allocated memory.\n. Arguments are: out, X, Y, A=1,x0=0, y0=0,sigma=0, b=0,b_x=0,b_y=0"},
    {"genSplitGaussInArray",  genSplitGaussInArray, METH_VARARGS | METH_KEYWORDS,
    "Generate a double Gaussian in pre-allocated memory.\n. Arguments are: out, X, Y, X1, Y1, A=1, A1=1,x0=0, y0=0,sigma=0, b=0,b_x=0,b_y=0"},
    {"genSplitGaussInArrayPVec",  genSplitGaussInArrayPVec, METH_VARARGS | METH_KEYWORDS,
    "Generate a double Gaussian in pre-allocated memory.\n. Arguments are: out, X, Y, X1, Y1, A=1, A1=1,x0=0, y0=0,sigma=0, b=0,b_x=0,b_y=0"},
     {"splitGaussWeightedMisfit",  splitGaussArrayPVecWeightedMisfit, METH_VARARGS | METH_KEYWORDS,
    "Generate a double Gaussian in pre-allocated memory.\n. Arguments are: out, X, Y, X1, Y1, A=1, A1=1,x0=0, y0=0,sigma=0, b=0,b_x=0,b_y=0"},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


PyMODINIT_FUNC initgauss_app(void)
{
    PyObject *m;

    m = Py_InitModule("gauss_app", gauss_appMethods);
    import_array()

    //SpamError = PyErr_NewException("spam.error", NULL, NULL);
    //Py_INCREF(SpamError);
    //PyModule_AddObject(m, "error", SpamError);
}