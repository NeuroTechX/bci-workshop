from OSC import *

import sys 
import time


class MuseServer(ThreadingOSCServer):
    """
    Server to receive Muse data through OSC, based on pyOSC.
    pyOSC has two versions (http://stackoverflow.com/questions/22135511/a-plethora-of-python-osc-modules-which-one-to-use)
    One works with Python 2.7, and the one on GitHub works with Python 3.0.
    
    First, make sure the Muse SDK is installed, and run muse-io in a console by 
    calling:
    muse-io --device Muse-XXXX --osc osc.udp://localhost:5000
    
    Inspired by http://developer.choosemuse.com/research-tools-example/grabbing-data-from-museio-a-few-simple-examples-of-muse-osc-servers
    """
    #listen for messages on port 5000
    def __init__(self, host='127.0.0.1', port=9999, printMsg=False):
        
        ThreadingOSCServer.__init__(self, server_address=(host,port))
        self.printMsg = printMsg
        self.configFound = False
        
    def startServer(self):
        self.addMsgHandler('/muse/eeg', self.format_eeg_handler)
        self.addMsgHandler('/muse/acc', self.format_acc_handler)
        self.addMsgHandler('muse/config', self.format_config_handler)

        self.addMsgHandler('muse/eeg/quantization', self.format_other_handler)
        self.addMsgHandler('muse/version', self.format_other_handler)
        self.addMsgHandler('muse/batt', self.format_other_handler)
        self.addMsgHandler('muse/drlref', self.format_other_handler)
        self.addMsgHandler('muse/elements', self.format_other_handler)     
        
        self.serve_forever()
            
    def format_eeg_handler(self, addr, tags, packet, source):
        if addr=='/muse/eeg':
            l_ear, l_forehead, r_forehead, r_ear = packet
            if self.printMsg:
                print '%s %f %f %f %f' % (addr, l_ear, l_forehead, r_forehead, r_ear)
                
    def format_acc_handler(self, addr, tags, packet, source):
        if addr=='/muse/acc':
            acc1, acc2, acc3 = packet
            if self.printMsg:
                print '%s %f %f %f' % (addr, acc1, acc2, acc3)
                
    def format_config_handler(self, addr, tags, packet, source):
        if addr=='/muse/config' and not self.configFound:
            self.config = packet
            self.configFound = True
            print qwfuibobs
                
    def format_other_handler(self, addr, tags, packet, source):
        pass

    def config_callback(self, path, args):
        if not self.configFound:
            self.config = args
            self.configFound = True
      
    def getMuseConfig(self):
        if self.configFound:
            out = self.config
            # TODO: Parse JSON!
        else:
            out = None
            
        return out
        

if __name__ == "__main__":
    
    try:
        server = MuseServer(printMsg=True)
        server.startServer()
        
    except 'allo':
        
        server.close()
        
        print str(err)
        sys.exit()