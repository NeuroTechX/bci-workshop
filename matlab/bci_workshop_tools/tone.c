/*==========================================================
 * tone.c - example in MATLAB External Interfaces
 *
 * Makes use of the function windows.h's Beep() to produce a tone with a 
 * given frequency in hertz (freq) and duration in miliseconds (duration)  
 * 
 * The calling syntax is:
 *
 *		tone(freq, duration)
 *
 * This is a MEX-file for MATLAB.
 * Based in the "Create C Source MEX-File" 
 * http://www.mathworks.com/help/matlab/matlab_external/standalone-example.html
 *
 * Raymundo Cassani
 *========================================================*/

#include "mex.h"
#include "windows.h"

/* The computational routine */
void tone(double freq, double duration)
{
/*Function Beep in windows.h */  
    Beep(freq,duration);
}

/* The gateway function */
void mexFunction( int nlhs, mxArray *plhs[],
                  int nrhs, const mxArray *prhs[])
{
    /* Variable declarations */
    double freq;              /* tone frequency in hertz */
    double duration;          /* tone duration in miliseconds */
    
    /* check for proper number of arguments */
    if(nrhs!=2) {
        mexErrMsgIdAndTxt("CassaniToolbox:tone:nrhs","Two inputs required.");
    }
    if(nlhs!=0) {
        mexErrMsgIdAndTxt("CassaniToolbox:tone:nlhs","None output required.");
    }
    /* make sure the two input arguments is scalar */
    if( !mxIsDouble(prhs[0]) || 
         mxIsComplex(prhs[0]) ||
         mxGetNumberOfElements(prhs[0])!=1 ||
         !mxIsDouble(prhs[1]) || 
         mxIsComplex(prhs[1]) ||
         mxGetNumberOfElements(prhs[1])!=1 ) {
        mexErrMsgIdAndTxt("CassaniToolbox:tone:notScalars","Both inputs must be scalar.");
    }
    
    /* get the values of the scalar inputs  */
    freq = mxGetScalar(prhs[0]);
    duration = mxGetScalar(prhs[1]);

    /* call the computational routine */
    tone(freq, duration);
}
