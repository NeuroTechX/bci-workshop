# -*- coding: utf-8 -*-
"""
Neurofeedback interface (Single-channel)

Description:

"""


import mules
import numpy as np
import matplotlib.pyplot as plt
import bci_workshop_tools as BCIw

if __name__ == "__main__":
    
    # MuLES connection parameters    
    mules_ip = '127.0.0.1'
    mules_port = 30000
    
    # Creates a mules_client
    mules_client = mules.MulesClient(mules_ip, mules_port) 
    # Device parameters    
    params = mules_client.getparams()

    # Experiment parameters
    eeg_buffer_secs = 5  # Size of the EEG data buffer (for Plot)  
    win_test_secs = 1     # Length of the Test Window in seconds
    overlap_secs = 0.5    # Overlap between two consecutive Test Windows
    shift_secs =win_test_secs - overlap_secs
    
    # Get name of features
    names_of_features = BCIw.feature_names(params['names of channels'])

    # Initialize EEG data buffer   
    eeg_buffer = np.zeros((params['sampling frequency']*eeg_buffer_secs, len(params['names of channels'])))  
    
    # Computes the number of Test Windows in the interval defined in "eeg_buffer_secs"
    n_win_test = int(np.floor((eeg_buffer_secs - win_test_secs) / float(shift_secs) + 1))
    
    # Initialize Feature data buffer
    feat_buffer = np.zeros((n_win_test, len(names_of_features)))
        
    # Initializes Plotters
    plotter_eeg = BCIw.dataPlotter(params['sampling frequency']*eeg_buffer_secs,
                                   params['names of channels'],
                                   params['sampling frequency'])
    
    plotter_feat = BCIw.dataPlotter(n_win_test,
                                    names_of_features,
                                    1 / float(shift_secs))
    
    mules_client.flushdata()  # Flush old data from MuLES       
 
    BCIw.beep() # Beep sound 
    print ' Press Ctrl-C in the console to break the While Loop'''
    try:    
        while True:    
            # Obtains EEG data from MuLES
            eeg_data = mules_client.getdata(shift_secs, False)
            # Updates EEG buffer
            eeg_buffer = BCIw.updatebuffer(eeg_buffer, eeg_data)
            # Plots EEG buffer        
            plotter_eeg.updatePlot(eeg_buffer) 
            # Gets newest "testing samples" from the buffer        
            test_data = BCIw.getlastdata(eeg_buffer, win_test_secs * params['sampling frequency'])
            # Computes features on "test_data" 
            feat_vector = BCIw.compute_feature_vector(test_data, params['sampling frequency'])
            # Fills in "feat_matrix"        
            feat_buffer = BCIw.updatebuffer(feat_buffer, np.asarray([feat_vector]))
            # Plots EEG buffer     
            plotter_feat.updatePlot((feat_buffer))     
            
            plt.pause(0.001)        
        
    except KeyboardInterrupt:
        # Close connection    
        mules_client.disconnect()

    