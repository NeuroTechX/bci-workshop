# -*- coding: utf-8 -*-
"""

BCI workshop 2015
Exercise 1: A neurofeedback interface (single-channel)

Description:
In this exercise, we'll try and play around with a simple interface that
receives EEG from one electrode, computes standard frequency band powers 
and displays both the raw signals and the features.


"""


import mules # The signal acquisition toolbox we'll use (MuLES)
import numpy as np # Module that simplifies computations on matrices 
import matplotlib.pyplot as plt # Module used for plotting
import bci_workshop_tools as BCIw # Bunch of useful functions for the workshop

if __name__ == "__main__":
    
    # MuLES connection parameters    
    mules_ip = '127.0.0.1'
    muse_port = 30000
    
    # Creates a mules_client
    mules_client = mules.MulesClient(mules_ip, muse_port) 
    params = mules_client.getparams() # Get the device parameters   
    

    # Set the experiment parameters ###########################################
    eeg_buffer_secs = 15  # Size of the EEG data buffer used for plotting the 
                          # signal (in seconds) 
    win_test_secs = 1     # Length of the window used for computing the features 
                          # (in seconds)
    overlap_secs = 0.7    # Overlap between two consecutive windows (in seconds)
    shift_secs = win_test_secs - overlap_secs
    index_channel = 1     # Index of the channnel to be used (with the Muse, we 
                          # can choose from 0 to 3)

    # This line changes params to work with only one electrode
    params['names of channels'] = ['CH1','STATUS']
    
    # Get name of features
    names_of_features = BCIw.feature_names(params['names of channels'])
    
    ###########################################################################

    
    # Initialize the buffers for storing raw EEG and features #################

    # Initialize raw EEG data buffer (for plotting)
    eeg_buffer = np.zeros((params['sampling frequency']*eeg_buffer_secs, 
                           len(params['names of channels']))) 
    
    # Compute the number of windows in "eeg_buffer_secs" (used for plotting)
    n_win_test = int(np.floor((eeg_buffer_secs - win_test_secs) / float(shift_secs) + 1))
    
    # Initialize the feature data buffer (for plotting)
    feat_buffer = np.zeros((n_win_test, len(names_of_features)))
        
    # Initializes the plots
    plotter_eeg = BCIw.dataPlotter(params['sampling frequency']*eeg_buffer_secs,
                                   params['names of channels'],
                                   params['sampling frequency'])
    
    plotter_feat = BCIw.dataPlotter(n_win_test,
                                    names_of_features,
                                    1/float(shift_secs))
                                    
    ###########################################################################
    
    
    mules_client.flushdata()  # Flush old data from MuLES       
    BCIw.beep() # Beep sound  
    
    
    # The try/except structure allows to quit the while loop by aborting the 
    # script with <Ctrl-C>
    try:    
        
        # The following loop does what we see in the diagram of Exercise 1:
        # acquire data, compute features, visualize the raw EEG and the features        
        while True:    
            
            """ 1- ACQUIRE DATA """
            eeg_data = mules_client.getdata(shift_secs, False) # Obtain EEG data from MuLES  
            eeg_data = eeg_data[:,[index_channel ,-1]] # Keep only one electrode (and the STATUS channel) for further analysis      
            eeg_buffer = BCIw.updatebuffer(eeg_buffer, eeg_data) # Update EEG buffer
            
            """ 2- COMPUTE FEATURES """
            # Get newest samples from the buffer 
            data_window = BCIw.getlastdata(eeg_buffer, win_test_secs * params['sampling frequency'])
            # Compute features on "data_window" 
            feat_vector = BCIw.compute_feature_vector(data_window, params['sampling frequency'])
            feat_buffer = BCIw.updatebuffer(feat_buffer, np.asarray([feat_vector])) # Update the feature buffer
            
            """ 3- VISUALIZE THE RAW EEG AND THE FEATURES """       
            plotter_eeg.updatePlot(eeg_buffer) # Plot EEG buffer     
            plotter_feat.updatePlot((feat_buffer)) # Plot the feature buffer 
            
            plt.pause(0.001)
            
    except KeyboardInterrupt:
        
        mules_client.disconnect() # Close connection
    