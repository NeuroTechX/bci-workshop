% Raymundo Cassani
% November 2015 
% 
% This file contains the MuLES class which hadles a TCP/IP connection to the 
% MuLES software, send commands, get data, send triggers among other functions.

classdef MulesClient < handle
    % This class represents a TCP/IP client for the MuLES software.
    properties
        ip            %the IP adress to be used to connect to the MuLES Server  
        port          %the port to use for a particular MuLES client. Every instance of MuLES should
%                     use a different port. To determine which port to use, please refer to the
%                     configuration file you are using for each instance of MuLES.
        client
        params
    end
    
    methods
        function self = MulesClient(ip, port)
%         Constructor method. This method connects to a MuLES Instance, request and 
%         retrieves the following information about the data acquisition device being used:
%             Device name
%             Device hardware
%             Sampling frequency (samples/second)
%             Data format
%             Number of channels
%             Extra parameters
            self.ip = ip;
            self.port = port;
      
%         TCP/IP connection
            self.connect();
            
%         Header information
            [dev_name, dev_hardware, fs, data_format, nCh] = self.getheader();
            channel_names = self.getnames();
            
%         Cell containing information about the device
            self.params = {dev_name,     ...     % device name
                          dev_hardware, ...     % device hardware
                          fs,           ...     % sampling frequency
                          data_format,  ...     % data format
                          nCh,          ...     % number of channels
                          channel_names};       % names of channels
        end
        
        function connect(self)
%         If, for some reason, the connection should be lost, this method can be used
%         to attempt to reconnect to the MuLES (Server). An exception is raised if the
%         reconnection attempt is unsuccessful.
            disp('Attempting connection');
            
%         Open a connection. 
            self.client = tcpip(self.ip, self.port, 'NetworkRole', 'client');
            self.client.InputBufferSize = 500000;
            self.client.Timeout = 5; %in seconds
            waiting_server = true;

            while waiting_server
                waiting_server = false;
                try
                    fopen(self.client);
                catch
                    waiting_server = true;
                end
                disp(['Connection with MuLES (', self.ip, ') was successful'] );
            end
        end
        
        function disconnect(self)
%         This method shuts down the connection to the MuLES
%         The connection parameters are preserved, so the connection can later be reestablished
%         by using the connect() method.

            fclose(self.client);
            disp('Connection closed successfully');

        end
        function kill(self)
%         This method send the command Kill to the MuLES software, which causes 
%         to end its execution
        self.sendcommand('K')
        end
        
        function sendcommand(self, command)
%         Sends an arbitrary command to the MuLES software.
%         Arguments:
%            command: the command to be sent.
        fwrite(self.client, command);
        end
        
        function flushdata(self)
%         Convenience method.         
%         This method flushes the data from the MuLES software. This is equivalent to calling
%         sendcommand('F').
        fwrite(self.client, 'F');
        disp('Flush Command');
        end
        
        function sendtrigger(self, trigger)
%         Send a trigger to the MuLES software.
%         Arguments:
%             trigger: the trigger to be sent, it has to be in the range [1 64].
         disp(['Trigger: ', num2str(trigger) , ' was sent']);
         fwrite(self.client,trigger,'uint8');          
        end
        
        function params = getparams(self)
%         Returns the data acquisition device's parameters. These are stored in a cell.
%
%             'device name'
%             'device hardware'
%             'sampling frequency'
%             'data format'
%             'number of channels'

         params = self.params;
        end
        
        function package = getmessage(self)
%         This gets a Message sent by MuLES an returns a byte array with the 
%         Message content
            nBytes_4B = fread(self.client, 4);  %How large is the package (# bytes)
            nBytes = double(swapbytes(typecast(uint8(nBytes_4B),'int32')));
            package = fread(self.client,nBytes);
        end
        
        function [dev_name, dev_hardware, fs, data_format, nCh] = getheader(self)
%          Request and Retrieves Header Information from MuLES 
             disp('Header request');
             self.sendcommand('H'); 
             [dev_name, dev_hardware, fs, data_format, nCh] = self.parseheader(char(self.getmessage())');
        end
        
        function [dev_name, dev_hardware, fs, data_format, nCh] = parseheader(self, package)
%         This function parses the Header Package sent by MuLES to obtain the
%         device's parameters. NAME, HARDWARE, FS, DATAFORMAT, #CH, EXTRA
%            
%         Argument:
%          package: Header package sent by MuLES.
            tmp = textscan(package,'%s','delimiter',',');
            cell_header = tmp{1};

            k = strncmp(cell_header, 'NAME',4);
            tmpcell = (textscan(char(cell_header(k)),'NAME=%s'));
            dev_name = char(tmpcell{1});

            k = strncmp(cell_header, 'HARDWARE',8);
            tmpcell = (textscan(char(cell_header(k)),'HARDWARE=%s'));
            dev_hardware = char(tmpcell{1});

            k = strncmp(cell_header, 'FS',2);
            fs = cell2mat(textscan(char(cell_header(k)),'FS=%f'));

            k = strncmp(cell_header, 'DATA',4);
            tmpcell = (textscan(char(cell_header(k)),'DATA=%s'));
            data_format = char(tmpcell{1});

            k = strncmp(cell_header, '#CH',3);
            nCh = cell2mat(textscan(char(cell_header(k)),'#CH=%d'));
        end
        
        function ch_labels = getnames(self)
%         Request and Retrieves the names of channels from MuLES 
            disp('Names Request');
            self.sendcommand('N');
            ch_names_str = char(self.getmessage())';
            tmp = textscan(ch_names_str,'%s','delimiter',',');
            ch_labels = tmp{1};
        end
        
        function data = getalldata(self)
%          Request and Retrieves ALL Data present in MuLES buffer 
%          (Data collected since the last Flush or last DataRequest)
%          in the shape  [samples, channels] 
            disp('Data Request');
            self.sendcommand('R');    
            data = self.parsedata(self.getmessage());  
        end
        
        function data = parsedata(self, package)
%          This function parses the Data Package sent by MuLES to obtain all the data 
%          available in MuLES as matrix of the size [n_samples, n_columns], therefore the
%          total of elements in the matrix is n_samples * n_columns. Each column represents
%          one channel
%             
%          Argument:
%          package: Data package sent by MuLES.

            sizeBytes = 4;
            nCh = numel(self.params{4});
            data_uint8 = uint8(package);
            dataPerSample = flipud(reshape(data_uint8,sizeBytes,[]));
            swapMesData = dataPerSample(:);
            preData = reshape(typecast(swapMesData,'single'),nCh,[])';
            data = [preData(:,1:nCh-1), single(typecast(preData(:,nCh),'int32'))]; 
        end
        
        function data_buffer = getdata(self, seconds, flush)
            % Returns a data_buffer with n_samples (fs * seconds)
            % Given that EEG DATA can come in multi-sample packages, the
            % size of ouput buffer can be larger than the required
            if nargin < 3
                flush = true;
            end
            if flush
                self.flushdata();
            end
          %Size of data requested
            n_samples = round(seconds * self.params{3});
            n_columns = numel(self.params{4});
            data_buffer = []; 
        
            while size(data_buffer,1) < n_samples %#Buffers is smaller that required
                new_data = self.getalldata();
                data_buffer = [data_buffer; new_data];
            end  
        end
    end
end

        