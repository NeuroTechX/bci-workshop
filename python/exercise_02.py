# -*- coding: utf-8 -*-
"""

BCI workshop 2015
Exercise 2: A Basic BCI

Description:
In this second exercise, we will learn how to use an automatic algorithm to
recognize somebody's mental states from their EEG. We will use a classifier:
a classifier is an algorithm that, provided some data, learns to recognize
patterns, and can then classify similar unseen information.

Change algorithm to GNB for better performance and uniformity with EEG 101
Add feature ranking plot (copy EEG 101)

"""

from pylsl import StreamInlet, resolve_byprop # What we'll use to read data from muse-lsl
import numpy as np # Module that simplifies computations on matrices
import matplotlib.pyplot as plt # Module used for plotting
import bci_workshop_tools as BCIw # Bunch of useful functions for the workshop

if __name__ == "__main__":

    # Search for active lsl EEG streams
    print("looking for an EEG stream...")
    streams = resolve_byprop('type', 'EEG', timeout=2)

    if len(streams) == 0:
        raise(RuntimeError, "Cant find EEG stream")

    # Set active EEG stream to inlet and apply time correction
    print("Start acquiring data")
    inlet = StreamInlet(streams[0], max_chunklen=12)
    eeg_time_correction = inlet.time_correction()

    # Get the stream info, description, sampling frequency, number of channels
    info = inlet.info()
    description = info.desc()
    freq = int(info.nominal_srate())
    num_channels = info.channel_count()

    # Get names of all channels
    ch = description.child('channels').first_child()
    ch_names = [ch.child_value('label')]
    for i in range(1, num_channels):
        ch = ch.next_sibling()
        ch_names.append(ch.child_value('label'))

    print(ch_names)

    #%% Set the experiment parameters

    training_secs = 20
    win_test_secs = 1     # Length of the Test Window in seconds
    overlap_secs = 0.7    # Overlap between two consecutive Test Windows
    shift_secs = win_test_secs - overlap_secs
    eeg_buffer_secs = 30  # Size of the EEG data buffer (duration of Testing section)


    #%% Record training data
    inlet = StreamInlet(streams[0], max_chunklen=12)
    eeg_time_correction = inlet.time_correction()

    # Record data for mental activity 0
    #eeg_data0 = np.zeros((freq*training_secs, num_channels))

    eeg_data0, timestamps0 = inlet.pull_chunk(timeout=20.0, max_samples=freq*training_secs)

    print('Close thine eyes!')


    # Record data for mental activity 1
    eeg_data1, timestamps1 = inlet.pull_chunk(timeout=20.0, max_samples=freq*training_secs)


    # Divide data into epochs
    eeg_epochs0 = BCIw.epoching(eeg_data0, win_test_secs * freq,
                                            overlap_secs * freq)
    eeg_epochs1 = BCIw.epoching(eeg_data1, win_test_secs * freq,
                                            overlap_secs * freq)

    #%% Compute features

    feat_matrix0 = BCIw.compute_feature_matrix(eeg_epochs0, freq)
    feat_matrix1 = BCIw.compute_feature_matrix(eeg_epochs1, freq)

    #%% Train classifier

    [classifier, mu_ft, std_ft] = BCIw.classifier_train(feat_matrix0, feat_matrix1, 'SVM')


    #%% Initialize the buffers for storing raw EEG and decisions

    eeg_buffer = np.zeros((freq*eeg_buffer_secs, len(params['data format'])))
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
            eeg_data = mules_client.getdata(shift_secs, False) # Obtain EEG data from MuLES
            eeg_buffer = BCIw.updatebuffer(eeg_buffer, eeg_data) # Update EEG buffer
            # Get newest "testing samples" from the buffer
            test_data = BCIw.getlastdata(eeg_buffer, win_test_secs * freq)

            """ 2- COMPUTE FEATURES and CLASSIFY"""
            # Compute features on "test_data"
            feat_vector = BCIw.compute_feature_vector(test_data, freq)
            y_hat = BCIw.classifier_test(classifier, feat_vector.reshape(1,-1), mu_ft, std_ft)

            decision_buffer = BCIw.updatebuffer(decision_buffer, np.reshape(y_hat,(-1,1)))

            """ 3- VISUALIZE THE DECISIONS"""
            print(str(y_hat))
            plotter_decision.updatePlot(decision_buffer) # Plot the decision buffer

            plt.pause(0.001)

    except KeyboardInterrupt:

        print('Closed!')
