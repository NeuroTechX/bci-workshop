# -*- coding: utf-8 -*-
"""
Exercise 1b: A neurofeedback interface (multi-channel)
======================================================

Description:
In this exercise, we'll try and play around with a simple interface that
receives EEG from multiple electrodes, computes standard frequency band
powers and displays both the raw signals and the features.

"""

from scipy import stats  # Module for statistics
import numpy as np  # Module that simplifies computations on matrices
import matplotlib.pyplot as plt  # Module used for plotting
from pylsl import StreamInlet, resolve_byprop  # Module to receive EEG data

import bci_workshop_tools as BCIw  # Our own functions for the workshop

# My own thread class for sending OSC Messages
from osc_messenger_thread import osc_messenger_thread

""" Constants to make my life easier """


class Band:
    Delta = 0
    Theta = 1
    Alpha = 2
    Beta = 3


class OSC_Path:
    Relax = '/avatar/parameters/osc_relax_avg'
    RelaxLeft = '/avatar/parameters/osc_relax_left'
    RelaxRight = '/avatar/parameters/osc_relax_right'
    Focus = '/avatar/parameters/osc_focus_avg'
    FocusLeft = '/avatar/parameters/osc_focus_left'
    FocusRight = '/avatar/parameters/osc_focus_right'


""" Paramaters to adjust: Rolling Average Weights """

relax_weight = 0.001
focus_weight = 0.01


""" Paramaters to adjust: Tuning Paramaters """
# normalize ratios between -1 and 1.
# Ratios are centered around 1.0. Tune scale to taste
offset = -1
relax_scale = 5
focus_scale = 2

""" Show EEG and Band Plots """
ENABLE_PLOTTER = False


rolling_Avg_Weights = {
    OSC_Path.Relax: relax_weight,
    OSC_Path.RelaxLeft: relax_weight,
    OSC_Path.RelaxRight: relax_weight,
    OSC_Path.Focus: focus_weight,
    OSC_Path.FocusLeft: focus_weight,
    OSC_Path.FocusRight: focus_weight
}

""" Normalize function to output values [-1 , 1] """


def tanh_normalize(data, scale, offset):
    return np.tanh(scale * (data + offset))


if __name__ == "__main__":

    # OSC messenger thread
    ip = "127.0.0.1"
    port = 9000
    send_rate = 0.001
    osc_thread = osc_messenger_thread(rolling_Avg_Weights, send_rate, ip, port)

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

    # Get the stream info, description, sampling frequency, number of channels
    info = inlet.info()
    description = info.desc()
    fs = int(info.nominal_srate())
    n_channels = info.channel_count()

    # Get names of all channels
    ch = description.child('channels').first_child()
    ch_names = [ch.child_value('label')]
    for i in range(1, n_channels):
        ch = ch.next_sibling()
        ch_names.append(ch.child_value('label'))
    ch_names = ['leftEar', 'leftForehead', 'rightForehead', 'rightEar']

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
    index_channel = [0, 1, 2, 3]
    # Name of our channel for plotting purposes
    ch_names = [ch_names[i] for i in index_channel]
    n_channels = len(index_channel)

    # Get names of features
    # ex. ['delta - CH1', 'pwr-theta - CH1', 'pwr-alpha - CH1',...]
    feature_names = BCIw.get_feature_names(ch_names)

    """3. INITIALIZE BUFFERS """

    # Initialize raw EEG data buffer (for plotting)
    eeg_buffer = np.zeros((int(fs * buffer_length), n_channels))
    filter_state = None  # for use with the notch filter

    # Compute the number of epochs in "buffer_length" (used for plotting)
    n_win_test = int(np.floor((buffer_length - epoch_length) /
                              shift_length + 1))

    # Initialize the feature data buffer (for plotting)
    feat_buffer = np.zeros((n_win_test, len(feature_names)))

    # Initialize the plots
    if ENABLE_PLOTTER:
        plotter_eeg = BCIw.DataPlotter(fs * buffer_length, ch_names, fs)
        plotter_feat = BCIw.DataPlotter(n_win_test, feature_names,
                                        1 / shift_length)

    """ 3. GET DATA """

    # The try/except structure allows to quit the while loop by aborting the
    # script with <Ctrl-C>
    print('Press Ctrl-C in the console to break the while loop.')

    try:
        # start OSC messenger loop
        osc_thread.start()

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

            """ Compute relax and focus metrics """
            # Split feature vector to the four respective bands
            # each band list has the band powers per channel
            band_vectors = [feat_vector[i::n_channels][1:-1]
                            for i in range(n_channels)]

            # Calculate Focus and Relax Ratios per channel
            relax_ratios = np.divide(
                band_vectors[Band.Theta], band_vectors[Band.Alpha])
            focus_ratios = np.divide(
                band_vectors[Band.Beta], band_vectors[Band.Theta])

            relax_normals = tanh_normalize(relax_ratios, relax_scale, offset)
            focus_normals = tanh_normalize(focus_ratios, focus_scale, offset)

            # band values are sorted from left to right channels.
            # Split arrays in half for left and right brain specific bands
            half_band_length = int(len(relax_normals) * 0.5)

            left_relax_normals = relax_normals[:half_band_length]
            right_relax_normals = relax_normals[half_band_length:]

            left_focus_normals = focus_normals[:half_band_length]
            right_focus_normals = focus_normals[half_band_length:]

            # average normalized values
            relax_avg = np.average(relax_normals, axis=0)
            relax_left = np.average(left_relax_normals, axis=0)
            relax_right = np.average(right_relax_normals, axis=0)

            focus_avg = np.average(focus_normals, axis=0)
            focus_left = np.average(left_focus_normals, axis=0)
            focus_right = np.average(right_focus_normals, axis=0)

            """ Send results to OSC messenger loop """
            osc_thread.set_message(OSC_Path.Relax, relax_avg)
            osc_thread.set_message(OSC_Path.RelaxLeft, relax_left)
            osc_thread.set_message(OSC_Path.RelaxRight, relax_right)

            osc_thread.set_message(OSC_Path.Focus, focus_avg)
            osc_thread.set_message(OSC_Path.FocusLeft, focus_left)
            osc_thread.set_message(OSC_Path.FocusRight, focus_right)

            """ 3.3 VISUALIZE THE RAW EEG AND THE FEATURES """
            if ENABLE_PLOTTER:
                plotter_eeg.update_plot(eeg_buffer)
                plotter_feat.update_plot(feat_buffer)
                plt.pause(0.00001)

    except KeyboardInterrupt:
        print('Closing!')
    finally:
        osc_thread.exit_flag = True
        osc_thread.join()
