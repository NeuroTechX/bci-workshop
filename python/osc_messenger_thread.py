import threading
import time

from collections import defaultdict
from pythonosc.udp_client import SimpleUDPClient


class osc_messenger_thread(threading.Thread):

    def __init__(self, weights_dict, send_rate, ip, port):
        threading.Thread.__init__(self)

        # osc client
        self.osc_client = SimpleUDPClient(ip, port)

        # rolling average dictionaries
        self.weights_dict = weights_dict
        self.current_value_dict = defaultdict(float)
        self.target_value_dict = defaultdict(float)

        # threading stuff
        self.send_rate = send_rate
        self.exit_flag = False

    def set_message(self, osc_path, value):
        self.target_value_dict[osc_path] = value

    def run(self):
        print('Running OSC Messenger')

        while not self.exit_flag:
            # calculate rolling averages
            for osc_path in self.target_value_dict:
                target_value = self.target_value_dict[osc_path]
                current_value = self.current_value_dict[osc_path]
                weight = self.weights_dict[osc_path]
                current_value = (1.0 - weight) * \
                    current_value + weight * target_value
                self.current_value_dict[osc_path] = current_value

            # send messages
            for osc_path, current_value in self.current_value_dict.items():
                self.osc_client.send_message(osc_path, current_value)

            time.sleep(self.send_rate)

    def __del__(self):
        self.exit_flag = True
