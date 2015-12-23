clear all
close all

% Set the experiment parameters
interval_1_secs = 15;
interval_2_secs = 15;

% MuLES connection parameters    
mules_ip = '127.0.0.1';
muse_port = 30000;

% Start Acquisition
mules_client = MulesClient(mules_ip, muse_port);  % Creates and Connect mules_client
params = mules_client.getparams(); % Get the device parameters
names = mules_client.getnames();
pause(1);

% Sending trigger 1    
mules_client.sendtrigger(1)

% Wait interval_1_sec
pause(interval_1_secs); %delay

% Sending trigger 2    
mules_client.sendtrigger(2)

% Wait interval_1_sec
pause(interval_2_secs); % delay  

% Sending trigger 1    
mules_client.sendtrigger(3)

% Close connection with MuLES
mules_client.disconnect() % Close connection