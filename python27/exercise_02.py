# -*- coding: utf-8 -*-
"""
MuLES Simple Client example
This script shows how to connect to MuLES and request EEG data 
Basic BCI
"""


import mules
import numpy as np
import bci_workshop_tools as BCIw
import matplotlib.pyplot as plt


if __name__ == "__main__":
    
    # MuLES connection paramters    
    mules_ip = '127.0.0.1'
    muse_port = 30000
    
    # Creates a mules_client
    mules_client = mules.MulesClient(mules_ip, muse_port) 
    # Device parameters    
    params = mules_client.getparams()
    fs = params['sampling frequency']
    
    #%% Set the experiment parameters
    
    training_secs = 20
    win_test_secs = 1     # Length of the Test Window in seconds
    overlap_secs = 0.7    # Overlap between two consecutive Test Windows
    shift_secs = win_test_secs - overlap_secs   
    eeg_buffer_secs = 30  # Size of the EEG data buffer (duration of Testing section) 
    
    
    #%% Record training data
    
    # Record data for mental activity 0
    BCIw.beep()
    eeg_data0 = mules_client.getdata(training_secs)
    
    # Record data for mental activity 1
    BCIw.beep()
    eeg_data1 = mules_client.getdata(training_secs)    
    
    # Divide data into epochs
    eeg_epochs0 = BCIw.epoching(eeg_data0, win_test_secs * params['sampling frequency'], 
                                            overlap_secs * params['sampling frequency'])
    eeg_epochs1 = BCIw.epoching(eeg_data1, win_test_secs * params['sampling frequency'],    
                                            overlap_secs * params['sampling frequency'])
    
    #%% Compute features
    
    feat_matrix0 = BCIw.compute_feature_matrix(eeg_epochs0, params['sampling frequency'])
    feat_matrix1 = BCIw.compute_feature_matrix(eeg_epochs1, params['sampling frequency'])

    #%% Train classifier    

    [classifier, mu_ft, std_ft] = BCIw.classifier_train(feat_matrix0, feat_matrix1, 'SVM')
    BCIw.beep(500,300)


    #%% Initialize the buffers for storing raw EEG and decisions
    
    eeg_buffer = np.zeros((params['sampling frequency']*eeg_buffer_secs, len(params['data format']))) 
    decision_buffer = np.zeros((30,1))

    mules_client.flushdata()  # Flushes old data from MuLES
    
    plotter_decision = BCIw.dataPlotter(30, ['Decision'])
    
    #BCIw.plot_classifier_training(feat_matrix0, feat_matrix1) # This will plot the decision boundary of a 2-feature SVM
    
    
    #%% Start pulling data and classifying in real-time
    
    BCIw.beep() # Beep sound
    
    # The try/except structure allows to quit the while loop by aborting the 
    # script with <Ctrl-C>
    print(' Press Ctrl-C in the console to break the While Loop')
    try:    
        
        while True: 
            
            """ 1- ACQUIRE DATA """
            eeg_data = mules_client.getdata(shift_secs, False)
            eeg_buffer = BCIw.updatebuffer(eeg_buffer, eeg_data)
            # Get newest "testing samples" from the buffer        
            test_data = BCIw.getlastdata(eeg_buffer, win_test_secs * params['sampling frequency'])

            """ 2- COMPUTE FEATURES and CLASSIFY"""            
            # Compute features on "test_data"
            feat_vector = BCIw.compute_feature_vector(test_data, params['sampling frequency'])
            y_hat = BCIw.classifier_test(classifier, feat_vector, mu_ft, std_ft)
            
            decision_buffer = BCIw.updatebuffer(decision_buffer, np.reshape(y_hat,(-1,1)))
            
            """ 3- VISUALIZE THE DECISIONS"""           
            print str(y_hat)
            plotter_decision.updatePlot(decision_buffer) # Plot the decision buffer
            
            plt.pause(0.001)
                 
    except KeyboardInterrupt:
        
        mules_client.disconnect() # Close connection 