# -*- coding: utf-8 -*-
"""

BCI workshop 2015
Exercise 1: A neurofeedback interface (single-channel)

Description:
In this exercise, we'll try and play around with a simple interface that
receives EEG from one electrode, computes standard frequency band powers
and displays both the raw signals and the features.

"""

from pylsl import StreamInlet, resolve_byprop  # Reads data from the Muse
import numpy as np  # Module that simplifies computations on matrices
import matplotlib.pyplot as plt  # Module used for plotting
import bci_workshop_tools as BCIw  # Bunch of useful functions for the workshop

if __name__ == "__main__":

    # Search for active lsl EEG streams
    print("looking for an EEG stream...")
    streams = resolve_byprop('type', 'EEG', timeout=2)

    print(len(streams))

    if len(streams) == 0:
        raise(RuntimeError, "Cant find EEG stream")

    # Set active EEG stream to inlet and apply time correction
    # TODO: explain time correction
    print("Start acquiring data")
    inlet = StreamInlet(streams[0], max_chunklen=12)
    eeg_time_correction = inlet.time_correction()

    # Get the stream info and description
    # TODO: Describe what exactly these contain
    info = inlet.info()
    description = info.desc()

    # Get the sampling frequency
    # This is an important value that represents how many EEG data points are
    # collected in a second. This influences our frequency band calculation
    freq = int(info.nominal_srate())

    """ SET EXPERIMENTAL PARAMETERS """

    # Length of the EEG data buffer (in seconds)
    # This buffer will hold last n seconds of data and be used for calculations
    buffer_length = 15

    # Length of the epochs used to perform the FFT (in seconds)
    epoch_length = 1

    # Amount of overlap between two consecutive epochs (in seconds)
    overlap_length = 0.5

    # Amount to 'shift' the start of each next consecutive epoch given overlap
    shift_length = epoch_length - overlap_length

    # Index of the channel (electrode) to be used
    # 0 = left ear, 1 = left forehead, 2 = right forehead, 3 = right ear
    index_channel = 1

    # Name of our channel for plotting purposes
    ch_name = ['CH1', 'Status']

    # Get names of features
    # ex. ['delta - CH1', 'pwr-theta - CH1', 'pwr-alpha - CH1',...]
    names_of_features = BCIw.feature_names(ch_name)

    """ INITIALIZE BUFFERS """

    # Initialize raw EEG data buffer (for plotting)
    eeg_buffer = np.zeros(freq*buffer_length)
    print(eeg_buffer.shape)

    # Compute the number of epochs in "buffer_length" (used for plotting)
    n_win_test = int(np.floor((buffer_length - epoch_length) /
                              float(shift_length) + 1))

    # Initialize the feature data buffer (for plotting)
    feat_buffer = np.zeros((n_win_test, len(names_of_features)))

    # Initialize the plots
    plotter_eeg = BCIw.dataPlotter(freq*buffer_length,
                                   ch_name,
                                   freq)

    plotter_feat = BCIw.dataPlotter(n_win_test,
                                    names_of_features,
                                    1 / float(shift_length))

    """ START GETTING DATA """

    # The try/except structure allows to quit the while loop by aborting the
    # script with <Ctrl-C>
    print(' Press Ctrl-C in the console to break the While Loop')
    try:

        # The following loop does what we see in the diagram of Exercise 1:
        # TODO: prepare this diagram
        # acquire data, compute features, visualize raw EEG and the features
        while True:

            """ 1- ACQUIRE DATA """
            # Obtain EEG data from muse-lsl stream
            eeg_data, timestamp = inlet.pull_chunk(timeout=1.0,
                                                   max_samples=12)

            # Remove all the channels except the one we're intersted in
            ch_data = [x[index_channel] for x in eeg_data]

            # Update EEG buffer
            eeg_buffer = BCIw.updatebuffer(eeg_buffer, ch_data)

            """ 2- COMPUTE FEATURES """
            # Get newest samples from the buffer
            data_epoch = eeg_buffer[-(epoch_length*freq):]
            print(data_epoch)

            # Compute features on "data_epoch"
            feat_vector = BCIw.compute_feature_vector(data_epoch, freq)
            feat_buffer = BCIw.updatebuffer(feat_buffer,
                                            np.asarray([feat_vector]))

            """ 3- VISUALIZE THE RAW EEG AND THE FEATURES """
            plotter_eeg.updatePlot(eeg_buffer)
            plotter_feat.updatePlot((feat_buffer))

            plt.pause(0.001)

    except KeyboardInterrupt:

        print('Closing!')
