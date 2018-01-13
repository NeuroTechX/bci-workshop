# -*- coding: utf-8 -*-
"""
Exercise 1: A neurofeedback interface (single-channel)
======================================================

Description:
In this exercise, we'll try and play around with a simple interface that
receives EEG from one electrode, computes standard frequency band powers
and displays both the raw signals and the features.

"""

import numpy as np  # Module that simplifies computations on matrices
import matplotlib.pyplot as plt  # Module used for plotting
from pylsl import StreamInlet, resolve_byprop  # Module to receive EEG data

import bci_workshop_tools as BCIw  # Our own functions for the workshop


if __name__ == "__main__":

    """ 1. CONNECT TO EEG STREAM """

    # Search for active LSL stream
    print('Looking for an EEG stream...')
    streams = resolve_byprop('type', 'EEG', timeout=2)
    if len(streams) == 0:
        raise RuntimeError('Can\'t find EEG stream.')

    # Set active EEG stream to inlet and apply time correction
    print("Start acquiring data")
    inlet = StreamInlet(streams[0], max_chunklen=12)
    eeg_time_correction = inlet.time_correction()

    # Get the stream info and description
    info = inlet.info()
    description = info.desc()

    # Get the sampling frequency
    # This is an important value that represents how many EEG data points are
    # collected in a second. This influences our frequency band calculation.
    fs = int(info.nominal_srate())

    """ 2. SET EXPERIMENTAL PARAMETERS """

    # Length of the EEG data buffer (in seconds)
    # This buffer will hold last n seconds of data and be used for calculations
    buffer_length = 15

    # Length of the epochs used to compute the FFT (in seconds)
    epoch_length = 1

    # Amount of overlap between two consecutive epochs (in seconds)
    overlap_length = 0.8

    # Amount to 'shift' the start of each next consecutive epoch
    shift_length = epoch_length - overlap_length

    # Index of the channel (electrode) to be used
    # 0 = left ear, 1 = left forehead, 2 = right forehead, 3 = right ear
    index_channel = [0]
    ch_names = ['ch1']  # Name of our channel for plotting purposes

    # Get names of features
    # ex. ['delta - CH1', 'pwr-theta - CH1', 'pwr-alpha - CH1',...]
    feature_names = BCIw.get_feature_names(ch_names)

    """ 3. INITIALIZE BUFFERS """

    # Initialize raw EEG data buffer (for plotting)
    eeg_buffer = np.zeros((int(fs * buffer_length), 1))
    filter_state = None  # for use with the notch filter

    # Compute the number of epochs in "buffer_length" (used for plotting)
    n_win_test = int(np.floor((buffer_length - epoch_length) /
                              shift_length + 1))

    # Initialize the feature data buffer (for plotting)
    feat_buffer = np.zeros((n_win_test, len(feature_names)))

    # Initialize the plots
    plotter_eeg = BCIw.DataPlotter(fs * buffer_length, ch_names, fs)
    plotter_feat = BCIw.DataPlotter(n_win_test, feature_names,
                                    1 / shift_length)

    """ 3. GET DATA """

    # The try/except structure allows to quit the while loop by aborting the
    # script with <Ctrl-C>
    print('Press Ctrl-C in the console to break the while loop.')

    try:
        # The following loop does what we see in the diagram of Exercise 1:
        # acquire data, compute features, visualize raw EEG and the features
        while True:

            """ 3.1 ACQUIRE DATA """
            # Obtain EEG data from the LSL stream
            eeg_data, timestamp = inlet.pull_chunk(
                    timeout=1, max_samples=int(shift_length * fs))

            # Only keep the channel we're interested in
            ch_data = np.array(eeg_data)[:, index_channel]

            # Update EEG buffer
            eeg_buffer, filter_state = BCIw.update_buffer(
                    eeg_buffer, ch_data, notch=True,
                    filter_state=filter_state)

            """ 3.2 COMPUTE FEATURES """
            # Get newest samples from the buffer
            data_epoch = BCIw.get_last_data(eeg_buffer,
                                            epoch_length * fs)

            # Compute features
            feat_vector = BCIw.compute_feature_vector(data_epoch, fs)
            feat_buffer, _ = BCIw.update_buffer(feat_buffer,
                                                np.asarray([feat_vector]))

            """ 3.3 VISUALIZE THE RAW EEG AND THE FEATURES """
            plotter_eeg.update_plot(eeg_buffer)
            plotter_feat.update_plot(feat_buffer)
            plt.pause(0.00001)

    except KeyboardInterrupt:
        print('Closing!')
