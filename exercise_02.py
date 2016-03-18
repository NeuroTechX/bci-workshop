# -*- coding: utf-8 -*-
"""
MuLES Simple Client example
This script shows how to connect to MuLES and request EEG data 
Basic BCI
"""


import mules
import numpy as np
import bci_workshop_tools as BCIw



if __name__ == "__main__":
    
    # MuLES connection paramters    
    mules_ip = '127.0.0.1'
    mules_port = 30000
    
    # Creates a mules_client
    mules_client = mules.MulesClient(mules_ip, mules_port) 
    # Device parameters    
    params = mules_client.getparams()
    fs = params['sampling frequency']
    
    # Experiment parameters
    training_secs = 20
    win_test_secs = 1     # Length of the Test Window in seconds
    overlap_secs = 0.7    # Overlap between two consecutive Test Windows
    shift_secs = win_test_secs - overlap_secs   
    eeg_buffer_secs = 30  # Size of the EEG data buffer (duration of Testing section)     
    
    # Gets data activity 0 (Usually Baseline)
    BCIw.beep()
    eeg_data0 = mules_client.getdata(training_secs)
    # Gets data activity 1 (Usually Task)
    BCIw.beep()
    eeg_data1 = mules_client.getdata(training_secs)    
    
    # Epoching
    eeg_epochs0 = BCIw.epoching(eeg_data0, win_test_secs * params['sampling frequency'], 
                                            overlap_secs * params['sampling frequency'])
    eeg_epochs1 = BCIw.epoching(eeg_data1, win_test_secs * params['sampling frequency'],    
                                            overlap_secs * params['sampling frequency'])
    
    # Computes features
    feat_matrix0 = BCIw.compute_feature_matrix(eeg_epochs0, params['sampling frequency'])
    feat_matrix1 = BCIw.compute_feature_matrix(eeg_epochs1, params['sampling frequency'])

    # Trains classifier    
    [classifier, mu_ft, std_ft] = BCIw.classifier_train(feat_matrix0, feat_matrix1, 'SVM')
    BCIw.beep(500,300)

    # Initializes EEG data buffer   
    eeg_buffer = np.zeros((params['sampling frequency']*eeg_buffer_secs, len(params['data format'])))   

    mules_client.flushdata()  # Flushes old data from MuLES
    
    BCIw.beep() # Beep sound   
    try:    
        while True: 
    #for iteration in range (0,iteration_limit):
            eeg_data = mules_client.getdata(shift_secs, False)
            # Update local data buffer
            eeg_buffer = BCIw.updatebuffer(eeg_buffer, eeg_data)
            # Get newest "testing samples" from the buffer        
            test_data = BCIw.getlastdata(eeg_buffer, win_test_secs * params['sampling frequency'])
            # Compute features on "test_data"
            feat_vector = BCIw.compute_feature_vector(test_data, params['sampling frequency'])
            y_hat = BCIw.classifier_test(classifier, feat_vector, mu_ft, std_ft )
            print str(y_hat)
            # Send info to other place
                 
    except KeyboardInterrupt:
        # Close connection    
        mules_client.disconnect()
        