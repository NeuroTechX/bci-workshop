#from liblo import *
import sys 
import time


class MuseServer(ServerThread):
    """
    Server to receive Muse data through OSC.    
    
    Inspired by http://developer.choosemuse.com/research-tools-example/grabbing-data-from-museio-a-few-simple-examples-of-muse-osc-servers
    """
    #listen for messages on port 5000
    def __init__(self, port=5000, printMsg=False):
        ServerThread.__init__(self, port)
        
        self.configFound = False

    #receive accelrometer data
    @make_method('/muse/acc', 'fff')
    def acc_callback(self, path, args):
        acc_x, acc_y, acc_z = args
        if printMsg:
            print "%s %f %f %f" % (path, acc_x, acc_y, acc_z)

    #receive EEG data
    @make_method('/muse/eeg', 'ffff')
    def eeg_callback(self, path, args):
        l_ear, l_forehead, r_forehead, r_ear = args
        if printMsg:
            print "%s %f %f %f %f" % (path, l_ear, l_forehead, r_forehead, r_ear)
            
    @make_method('/muse/config', 's')
    def config_callback(self, path, args):
        if not self.configFound:
            self.config = args
            self.configFound = True
            # TODO: TRANSFORM JSON TO DICTIONARY!!!

    #handle unexpected messages
    @make_method(None, None)
    def fallback(self, path, args, types, src):
        if printMsg:
            print "Unknown message \
            \n\t Source: '%s' \
            \n\t Address: '%s' \
            \n\t Types: '%s ' \
            \n\t Payload: '%s'" \
            % (src.url, path, types, args)   
      
    def getparams(self):
        if self.configFound:
            out = self.config
        else:
            out = None
            
        return out
        

if __name__ == "__main__":
    
    try:
        server = MuseServer()
        
    except ServerError, err:
        print str(err)
        sys.exit()
    
    server.start()
    
    while 1:
        time.sleep(1)