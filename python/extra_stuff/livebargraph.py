#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 25 21:11:45 2017

@author: hubert
"""

import numpy as np
import matplotlib.pyplot as plt


class LiveBarGraph(object):
    """
    """
    def __init__(self, band_names=['delta', 'theta', 'alpha', 'beta'],
                 ch_names=['TP9', 'AF7', 'AF8', 'TP10']):
        """
        """
        self.band_names = band_names
        self.ch_names = ch_names
        self.n_bars = self.band_names * self.ch_names

        self.x =

        self.fig, self.ax = plt.subplots()
        self.ax.set_ylim((0, 1))

        y = np.zeros((self.n_bars,))
        x = range(self.n_bars)

        self.rects = self.ax.bar(x, y)

    def update(self, new_y):
        [rect.set_height(y) for rect, y in zip(self.rects, new_y)]


if __name__ == '__main__':

    bar = LiveBarGraph()
    plt.show()

    while True:
        bar.update(np.random.random(10))
        plt.pause(0.1)





