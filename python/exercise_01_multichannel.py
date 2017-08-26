# -*- coding: utf-8 -*-
"""

BCI workshop 2015
Exercise 1b: A neurofeedback interface (multi-channel)

Description:
In this exercise, we'll try and play around with a simple interface that
receives EEG from mulitple electrodes, computes standard frequency band powers
and displays both the raw signals and the features.

This multi-channel version could be the 'exercise' after working throught the exercise 01 script

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
    eeg_buffer_secs = 15  # Size of the EEG data buffer used for plotting the
                          # signal (in seconds)
    win_test_secs = 1     # Length of the window used for computing the features
                          # (in seconds)
    overlap_secs = 0.5    # Overlap between two consecutive windows (in seconds)
    shift_secs = win_test_secs - overlap_secs
    index_channel = 1     # Index of the channnel to be used (with the Muse, we
                          # can choose from 0 to 3)

    # Get name of features
    names_of_features = BCIw.feature_names(ch_names)

    #%% Initialize the buffers for storing raw EEG and features

    # Initialize raw EEG data buffer (for plotting)
    eeg_buffer = np.zeros((freq*eeg_buffer_secs, num_channels))

    # Compute the number of windows in "eeg_buffer_secs" (used for plotting)
    n_win_test = int(np.floor((eeg_buffer_secs - win_test_secs) / float(shift_secs) + 1))

    # Initialize the feature data buffer (for plotting)
    feat_buffer = np.zeros((n_win_test, len(names_of_features)))

    # Initialize the plots
    plotter_eeg = BCIw.dataPlotter(freq*eeg_buffer_secs,
                                   ch_names,
                                   freq)

    plotter_feat = BCIw.dataPlotter(n_win_test,
                                    names_of_features,
                                    1 / float(shift_secs))

    #%% Start pulling data

    # The try/except structure allows to quit the while loop by aborting the
    # script with <Ctrl-C>
    print(' Press Ctrl-C in the console to break the While Loop')
    try:

        # The following loop does what we see in the diagram of Exercise 1:
        # acquire data, compute features, visualize the raw EEG and the features
        while True:

            # TODO: Change line plot for features to grouped bar chart

            """ 1- ACQUIRE DATA """
            eeg_data, timestamp = inlet.pull_chunk(timeout=1.0,
                                               max_samples=12)  # Obtain EEG data from muse-lsl

            eeg_buffer = BCIw.updatebuffer(eeg_buffer, eeg_data) # Update EEG buffer

            """ 2- COMPUTE FEATURES """
            # Get newest samples from the buffer
            data_window = BCIw.getlastdata(eeg_buffer, win_test_secs * freq)

            print(data_window)

            # Compute features on "data_window"
            feat_vector = BCIw.compute_feature_vector(data_window, freq)
            feat_buffer = BCIw.updatebuffer(feat_buffer, np.asarray([feat_vector])) # Update the feature buffer

            """ 3- VISUALIZE THE RAW EEG AND THE FEATURES """
            plotter_eeg.updatePlot(eeg_buffer) # Plot EEG buffer
            plotter_feat.updatePlot((feat_buffer)) # Plot the feature buffer

            plt.pause(0.001)

    except KeyboardInterrupt:

        print('Closing!')
