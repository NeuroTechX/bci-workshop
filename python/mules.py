'''
Authors: Alexandre Drouin-Picaro and Raymundo Cassani
April 2015

This file contains the MuLES class which handles a TCP/IP connection to the
MuLES software, send commands, get data, send triggers among other functions.

Methods:
    __init__(ip, port)
    connect()
    disconnect()
    kill()
    sendcommand(command)
    flushdata()
    sendtrigger(trigger)
    getparam()
    getfs()
    getdevicename()
    getmessage()
    getheadder()
    parseheader(package)
    getnames()
    getalldata()
    parsedata(package)
    getdata(seconds, flush)

'''

import socket
import numpy as np
import array
import struct
import sys

class MulesClient():
    """
    This class represents a TCP/IP client for the MuLES software.

    """

    def __init__(self, ip, port):
        """
        Constructor method. This method connects to a MuLES Instance, request and
        retrieves the following information about the data acquisition device being used:
            Device name
            Device hardware
            Sampling frequency (samples/second)
            Data format
            Number of channels
            Extra parameters

        Arguments:
            ip: the IP adress to be used to connect to the MuLES Server.
            port: the port to use for a particular MuLES client. Every instance of MuLES should
                use a different port. To determine which port to use, please refer to the
                configuration file you are using for each instance of MuLES.
        """
        self.ip = ip
        self.port = port
        self.python2 = sys.version_info < (3,0)

        # TCP/IP connection
        self.connect()
        # Header information
        dev_name, dev_hardware, fs, data_format, nCh = self.getheader()
        channel_names = self.getnames()
        # Dictionary containing information about the device
        self.params = {'device name': dev_name,
                       'device hardware': dev_hardware,
                       'sampling frequency': int(fs),
                       'data format': data_format,
                       'number of channels': nCh,
                       'names of channels': channel_names}


    def connect(self):
        """
        If, for some reason, the connection should be lost, this method can be used
        to attempt to reconnect to the MuLES (Server). An exception is raised if the
        reconnection attempt is unsuccessful.
        """
        print('Attempting connection')
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((self.ip, self.port))
            print('Connection successful')
        except:
            self.client = None
            print('Connection attempt unsuccessful')
            raise

    def disconnect(self):
        """
        This method shuts down the connection to the MuLES and sets client to None.
        The connection parameters are preserved, so the connection can later be reestablished
        by using the connect() method.
        """
        self.client.close()
        self.client = None
        print('Connection closed successfully')

    def kill(self):
        """
        This method send the command Kill to the MuLES software, which causes
        to end its execution
        """
        self.sendcommand('K')

    def sendcommand(self, command):
        """
        Sends an arbitrary command to the MuLES software.

        Arguments:
            command: the command to be sent.
        """
        if self.python2:
            self.client.send(command)
        else:
            self.client.send(bytearray(command,'ISO-8859-1'))


    def flushdata(self):
        """
        Convenience method.

        This method flushes the data from the MuLES software. This is equivalent to calling
        sendcommand('F').
        """
        self.sendcommand('F')

    def sendtrigger(self, trigger):
        """
        Send a trigger to the MuLES software.

        Arguments:
            trigger: the trigger to be sent, it has to be in the range [1 64].
        """
        print('Trigger: ' + str(trigger) + ' was sent')
        self.sendcommand(chr(trigger))

    def getparams(self):
        """
        Returns the data acquisition device's parameters. These are stored in a dictionary.
        To obtain a value from the dictionary, the following strings should be used:
            'device name'
            'device hardware'
            'sampling frequency'
            'data format'
            'number of channels'

        Returns:
            A dictionary containing information about the device.
        """
        return self.params

    def getfs(self):
        """
            Retrieves sampling frequency 'fs' [Hz]
        """
        return self.params['sampling frequency']

    def getdevicename(self):
        """
            Retrieves the name of the device
        """
        return self.params['device name']

    def getmessage(self):
        """
            This gets a Message sent by MuLES an returns a byte array with the
            Message content
        """
        n_bytes_4B = array.array('B',self.client.recv(4) )
        n_bytes = struct.unpack('i',n_bytes_4B[::-1])[0]
        #n_bytes equals to number of bytes to read from the connection
        #[0] is used to get an int32 rather than turple
        # Next while lopp secures the integrity of the package
        package = '';

        while len(package) < n_bytes:
            if self.python2:
                package += self.client.recv(1)
            else:
                package += self.client.recv(1).decode("ISO-8859-1")

        return package

    def getheader(self):
        """
            Request and Retrieves Header Information from MuLES
        """
        #print('Header request')
        self.sendcommand('H')
        return self.parseheader(self.getmessage())

    def parseheader(self, package):
        """
            This function parses the Header Package sent by MuLES to obtain the
            device's parameters. NAME, HARDWARE, FS, DATAFORMAT, #CH, EXTRA

            Argument:
            package: Header package sent by MuLES.
        """

        array_header = package.split(',')
        for field in array_header:
            if field.find('NAME') != -1:
                ind = field.find('NAME')
                dev_name = field[ind+len('NAME='):]
            elif field.find('HARDWARE') != -1:
                ind = field.find('HARDWARE')
                dev_hardware = field[ind+len('HARDWARE='):]
            elif field.find('FS') != -1:
                ind = field.find('FS')
                fs = float(field[ind+len('FS='):])
            elif field.find('DATA') != -1:
                ind = field.find('DATA')
                data_format = field[ind+len('DATA='):]
            elif field.find('#CH') != -1:
                ind = field.find('#CH')
                nCh = int(field[ind+len('#CH='):])

        return dev_name, dev_hardware, fs, data_format, nCh

    def getnames(self):
        """
            Request and Retrieves the names of channels from MuLES
        """
        #print('Names Request')
        self.sendcommand('N')
        return self.getmessage().split(',')


    def getalldata(self):
        """
            Request and Retrieves ALL Data present in MuLES buffer
            (Data collected since the last Flush or last DataRequest)
            in the shape
            [samples, channels]
        """
        #print('Data Request')
        self.sendcommand('R')
        return self.parsedata(self.getmessage())

    def parsedata(self, package):
        """
            This function parses the Data Package sent by MuLES to obtain all the data
            available in MuLES as matrix of the size [n_samples, n_columns], therefore the
            total of elements in the matrix is n_samples * n_columns. Each column represents
            one channel

            Argument:
            package: Data package sent by MuLES.
        """
        size_element = 4           # Size of each one of the elements is 4 bytes

        n_columns = len(self.params['data format'])
        n_bytes = len(package)
        n_samples = (n_bytes/size_element) / n_columns
        ####mesData = np.uint8(mesData) # Convert from binary to integers (not necessary pyton)
        if self.python2:
            bytes_per_element = np.flipud(np.reshape(list(bytearray(package)), [size_element,-1],order='F'))
        else:
            bytes_per_element = np.flipud(np.reshape(list(bytearray(package, 'ISO-8859-1'), ), [size_element,-1],order='F'))
        # Changes "package" to a list with size (n_bytes,1)
        # Reshapes the list into a matrix bytes_per_element which has the size: (4,n_bytes/4)
        # Flips Up-Down the matrix of size (4,n_bytes/4) to correct the swap in bytes

        package_correct_order = np.uint8(np.reshape(bytes_per_element,[n_bytes,-1],order='F' ))
        # Unrolls the matrix bytes_per_element, in "package_correct_order"
        # that has a size (n_bytes,1)

        data_format_tags = self.params['data format']*int(n_samples)
        # Tags used to map the elements into their corresponding representation
        package_correct_order_char = "".join(map(chr,package_correct_order))

        if self.python2:
            elements = struct.unpack(data_format_tags,package_correct_order_char)
        else:
            elements = struct.unpack(data_format_tags, bytearray(package_correct_order_char,'ISO-8859-1'))
        # Elements are cast in their corresponding representation
        data = np.reshape(np.array(elements),[n_samples,n_columns],order='C')
        # Elements are reshap into data [n_samples, n_columns]

        return data

    def getdata(self, seconds, flush=True ):
        """
            Flush all the Data present in MuLES buffer and,
            Request and Retrieve a certain amount of Data indicated as seconds
            Data returned has the shape [seconds * sampling_frequency, channels]

            Argument:
            seconds: used to calculate the amount of samples requested n_samples
                     n_samples = seconds * sampling_frequency
            flush:   Boolean, if True send the command Flush before getting Data,
                     Defaul = True
        """
        if flush:
            self.flushdata()

        # Size of data requested
        n_samples = int(round(seconds * self.params['sampling frequency']))
        n_columns = len(self.params['data format'])
        data_buffer = -1 * np.ones((n_samples, n_columns))

        while (data_buffer[0, n_columns - 1]) < 0 : #While the first row has not been rewriten
            new_data = self.getalldata()
            new_samples = new_data.shape[0]
            data_buffer = np.concatenate((data_buffer, new_data), axis =0)
            data_buffer = np.delete(data_buffer, np.s_[0:new_samples], 0)

        return data_buffer
