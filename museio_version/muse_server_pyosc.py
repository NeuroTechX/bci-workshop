from OSC import *

import sys 
import time


class MuseServer(ThreadingOSCServer):
    """
    Server to receive Muse data through OSC, based on pyOSC.
    pyOSC has two versions (http://stackoverflow.com/questions/22135511/a-plethora-of-python-osc-modules-which-one-to-use)
    One works with Python 2.7, and the one on GitHub works with Python 3.0
    
    First, make sure the Muse SDK is installed, and run muse-io in a console by 
    calling:
    muse-io --device Muse-XXXX --osc osc.udp://localhost:5000
    
    Inspired by http://developer.choosemuse.com/research-tools-example/grabbing-data-from-museio-a-few-simple-examples-of-muse-osc-servers
    """
    #listen for messages on port 5000
    def __init__(self, host='127.0.0.1', port=5060, printMsg=False):
        
        ThreadingOSCServer.__init__(self, server_address=(host,port))  
        self.serve_forever()
        self.configFound = False
        
        self.addMsgHandler("/muse/eeg", self.format_eeg_handler)

    
    #receive accelerometer data
#    @make_method('/muse/acc', 'fff')
#    def acc_callback(self, path, args):
#        acc_x, acc_y, acc_z = args
#        if printMsg:
#            print "%s %f %f %f" % (path, acc_x, acc_y, acc_z)
            
    def format_eeg_handler(addr, tags, packet, source):
        if addr=='/muse/eeg':
            l_ear, l_forehead, r_forehead, r_ear = packet
            if printMsg:
                print "%s %f %f %f %f" % (addr, l_ear, l_forehead, r_forehead, r_ear)
#
#    #receive EEG data
#    @make_method('/muse/eeg', 'ffff')
#    def eeg_callback(self, path, args):
#        l_ear, l_forehead, r_forehead, r_ear = args
#        if printMsg:
#            print "%s %f %f %f %f" % (path, l_ear, l_forehead, r_forehead, r_ear)
#            
#    @make_method('/muse/config', 's')
#    def config_callback(self, path, args):
#        if not self.configFound:
#            self.config = args
#            self.configFound = True
#            # TODO: TRANSFORM JSON TO DICTIONARY!!!
#
#    #handle unexpected messages
#    @make_method(None, None)
#    def fallback(self, path, args, types, src):
#        if printMsg:
#            print "Unknown message \
#            \n\t Source: '%s' \
#            \n\t Address: '%s' \
#            \n\t Types: '%s ' \
#            \n\t Payload: '%s'" \
#            % (src.url, path, types, args)   
      
    def getparams(self):
        if self.configFound:
            out = self.config
        else:
            out = None
            
        return out
        

if __name__ == "__main__":
    
    try:
        server = MuseServer(printMsg=True)
        
    except 'allo':
        
        server.close()
        
        print str(err)
        sys.exit()
    
#    try:
#        server = MuseServer(printMsg=True)
#        
#    
#    server.start()
#    
#    while 1:
#        time.sleep(1)