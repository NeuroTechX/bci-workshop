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

mules_client.flushdata();
for i = 1:500
    eeg_data = mules_client.getdata(1,false);
    plot(eeg_data);
    pause(0.00001);
end

% Close connection with MuLES
mules_client.disconnect() % Close connection