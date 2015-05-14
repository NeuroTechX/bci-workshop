# -*- coding: utf-8 -*-
"""
BCI Workshop Auxiliary Tools

Created on Fri May 08 15:34:59 2015

@author: Cassani
"""

import matplotlib.pyplot as plt
import numpy as np
from sklearn import svm
import winsound



def plotmultichannel(data, params=None): 
# TODO Receive Labels as arguments
    """
    Creates a plot to present multichannel data
    
    Arguments
    data:  Multichannel Data [n_samples, n_channels]
    params: information about the data acquisition device being
    """  
    plt.figure()        

    n_samples = data.shape[0]
    n_channels = data.shape[1]
    
    if params is not None:
        fs = params['sampling frequency']
        names = params['names of channels']
    else:
        fs = 1
        names = [""] * n_channels
    
    time_vec = np.arange(n_samples) / float(fs)

    data = np.fliplr(data)
    offset = 0
    for i_channel in range (0, n_channels):
        data_ac = data[:,i_channel] - np.mean(data[:,i_channel])
        offset = offset + 2 * np.max(np.abs(data_ac))        
        plt.plot(time_vec, data_ac + offset, label=names[i_channel])        

    plt.xlabel('Time [s]');
    plt.ylabel('Amplitude');
    plt.legend()        
    plt.draw()
    
def epoching(data, samples_epoch, samples_overlap = 0):
    """
    Given a 2D array of the shape [n_samples, n_channels]    
    Creates a 3D array of the shape [wlength_samples, n_channels, n_epochs]
    
    Arguments
    data:  2D Data [n_samples, n_channels]
    samples_epoch: Window length in samples
    samples_overlap: Overlap between windows in samples, if it is not specified
                     samples_overlap = 0
    """  

    n_samples = data.shape[0]
    n_channels = data.shape[1]

    samples_shift = samples_epoch - samples_overlap

    n_epochs =  int(np.floor( (n_samples - samples_epoch) / float(samples_shift) ) + 1 )

    #markers indicates where the epoch starts, and the epoch contains samples_epoch rows
    markers = np.asarray(range(0,n_epochs + 1)) * samples_shift;
    markers = markers.astype(int)
    #Divide data in epochs
    epochs = np.zeros((samples_epoch, n_channels, n_epochs));

    for i_epoch in range(0,n_epochs):
        epochs[:,:,i_epoch] = data[ markers[i_epoch] : markers[i_epoch] + samples_epoch ,:]
        
    if (markers[-1] != n_samples): 
        remainder = data[markers[-1] : n_samples, :]
    else:
        remainder = np.asarray([])
    
    return epochs #, remainder
    
def compute_feature_vector(eegdata, Fs):
    """Extract the features from the EEG
        Inputs:
          eegdata: array of dimension [number of samples, number of channels]
          Fs: sampling frequency of eegdata

        Outputs:
          feature_vector: [number of features points; number of different features

    """
    #Delete last column (Status)
    eegdata = np.delete(eegdata, -1 , 1)    
        
    # 1. Compute the PSD
    winSampleLength, nbCh = eegdata.shape
    
    # Apply Hamming window
    w = np.hamming(winSampleLength)
    dataWinCentered = eegdata - np.mean(eegdata, axis=0) # Remove offset
    dataWinCenteredHam = (dataWinCentered.T*w).T

    NFFT = nextpow2(winSampleLength)
    Y = np.fft.fft(dataWinCenteredHam, n=NFFT, axis=0)/winSampleLength
    PSD = 2*np.abs(Y[0:NFFT/2,:])
    f = Fs/2*np.linspace(0,1,NFFT/2)     
            
    # SPECTRAL FEATURES
    # Average of band powers
    # Delta <4
    ind_delta, = np.where(f<4)
    meanDelta = np.mean(PSD[ind_delta,:],axis=0)
    # Theta 4-8
    ind_theta, = np.where((f>=4) & (f<=8))
    meanTheta = np.mean(PSD[ind_theta,:],axis=0)
    # Alpha 8-12
    ind_alpha, = np.where((f>=8) & (f<=12)) 
    meanAlpha = np.mean(PSD[ind_alpha,:],axis=0)
    # Beta 12-30
    ind_beta, = np.where((f>=12) & (f<30))
    meanBeta = np.mean(PSD[ind_beta,:],axis=0)
    
    feature_vector = np.concatenate((meanDelta, meanTheta, meanAlpha, meanBeta),
                                    axis=0)
    
    feature_vector = np.log10(feature_vector)   
       
    return feature_vector
        
def nextpow2(i):
        """ Find the next power of 2 for number i """
        n = 1
        while n < i: 
            n *= 2
        return n
        
def compute_feature_matrix(epochs, Fs):
    """
    Calls compute_feature_vector for each EEG epoch contained in the "epochs"
    
    """
    n_epochs = epochs.shape[2]
        
    # Feature Matrix size
    feature_matrix = np.zeros((n_epochs, 40))    
    
        
    for i_epoch in range(0,n_epochs):
        feature_matrix[i_epoch, :] = compute_feature_vector(epochs[:,:,i_epoch], Fs).T 

    return feature_matrix     
    
    
def classifier_train(feature_matrix_0, feature_matrix_1, algorithm = 'SVM'):
    """
        Trains a binary classifier using the SVM algorithm with the following parameters
        
        
        Arguments
        feature_matrix_0: Matrix with examples for Class 0
        feature_matrix_0: Matrix with examples for Class 1
        algorithm: Currently only SVM is supported
    """
    # Create vector Y (class labels)
    class0 = np.zeros((feature_matrix_0.shape[0],1))
    class1 = np.ones((feature_matrix_1.shape[0],1))
    
    # Concatenate feature matrices and their respective labels
    y = np.concatenate((class0, class1),axis=0)
    features_all = np.concatenate((feature_matrix_0, feature_matrix_1),axis=0)
    # Normalize inputs

    mu_ft = np.mean(features_all)
    std_ft = np.std(features_all)
    X = (features_all - mu_ft) / std_ft
    # Train SVM, using defualt parameters     
    classifier = svm.SVC()
    classifier.fit(X, y)     
    # Return the classfier trained and the normalization parameters
    
    return classifier, mu_ft, std_ft

def classifier_test(classifier, feature_vector, mu_ft, std_ft):
    # Normalize feature_vector
    x = (feature_vector - mu_ft) / std_ft    
    y_hat = classifier.predict(x)
    #y_hat = None
    return y_hat
    
def beep(f=500, d=500):
    """
        Uses the Sound-playing interface for Windows to play a beep
        
        Arguments
    f: Frequency of the beep in Hz
    d: Duration of the beep in ms
    """
    winsound.Beep(f,d)
    
def feature_names(ch_names):
    """
        Generate the name of the features
        
        Arguments
    ch_names: List with Electrode names
    """
    bands = ['pwr-delta', 'pwr-theta', 'pwr-alpha' ,'pwr-beta']

    feat_names = []
    for band in bands:
        for ch in range(0,len(ch_names)-1):
        #Last column is ommited because it is the Status Channel
            feat_names.append(band + '-' + ch_names[ch])
            
    return feat_names 
            
    
def updatebuffer(data_buffer, new_data):
    """
        Concatenates "new_data" into "buffer_array", and returns an array with 
        the same size than "buffer_array" 
    """    
    
    new_samples = new_data.shape[0]
    new_buffer = np.concatenate((data_buffer, new_data), axis =0)
    new_buffer = np.delete(new_buffer, np.s_[0:new_samples], 0)
    
    return new_buffer
    
    
    
def getlastdata(data_buffer, newest_samples):
    """
        Obtains from "buffer_array" the "newest samples" (N rows from the bottom of the buffer)
    """
    new_buffer = data_buffer[(data_buffer.shape[0] - newest_samples)::,::]  

    return new_buffer  
    
    
class dataPlotter():
    """ Plot EEG/features data"""
    
    def __init__(self, nbPoints, chNames, fs=None, title=None):
        """Initialize the figure"""
        
        self.nbPoints = nbPoints
        self.chNames = chNames
        self.nbCh = len(self.chNames)
                                
        if fs is None:   # Verify Sampling frequency
            self.fs = 1
        else:
            self.fs = fs
            
        if title is None:
            self.figTitle = ''
        else:
            self.figTitle = title
                    
                    
        data = np.empty((self.nbPoints,1))*np.nan
        self.t = np.arange(data.shape[0])/float(self.fs)
        
        # Create offset parameters for plotting multiple signals
        self.yAxisRange = 100
        self.chRange = self.yAxisRange/float(self.nbCh)
        self.offsets = np.round((np.arange(self.nbCh)+0.5)*(self.chRange))
        
        # Create the figure and axis
        plt.ion()
        self.fig = plt.figure()
        self.ax =  plt.subplot()
        #self.ax.set_xticks([])
        self.ax.set_yticks(self.offsets)
        self.ax.set_yticklabels(self.chNames)
        #self.ax.yaxis.set_ticks(self.chNames)
        
        # Initialize the figure
        plt.title(self.figTitle)
        
        self.chLinesDict = {}
        for i, chName in enumerate(self.chNames):
            self.chLinesDict[chName], = plt.plot(self.t, data+self.offsets[i], label=chName)
            
        #plt.legend()
        plt.xlabel('Time')
        plt.ylim([0, self.yAxisRange])
        plt.xlim([np.min(self.t), np.max(self.t)])
        
        plt.show()
        plt.pause(0.1)
    
    def updatePlot(self, data):
        """ Update the plot """
        
        plt.figure(self.fig.number)  
        assert (data.shape[1] == self.nbCh), 'new data does not have the same number of channels'
        assert (data.shape[0] == self.nbPoints), 'new data does not have the same number of points'

        data = data - np.mean(data,axis=0)
        std_data = np.std(data,axis=0)
        std_data[np.where(std_data == 0)] = 1
        data = data/std_data*self.chRange/5.0     
        
        for i, chName in enumerate(self.chNames):
            self.chLinesDict[chName].set_ydata(data[:,i]+self.offsets[i])
        
        plt.draw()
    
    def clear(self):
        """ Clear the figure """
        
        blankData = np.empty((self.nbPoints,1))*np.nan
        
        for i, chName in enumerate(self.chNames):
            self.chLinesDict[chName].set_ydata(blankData)
        
        plt.draw()
    
    def close(self):
        """ Close the figure """
        
        plt.close(self.fig)
