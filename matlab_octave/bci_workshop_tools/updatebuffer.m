function new_buffer = updatebuffer( data_buffer, new_data )
%UPDATEBUFFER:
% Concatenates "new_data" into "buffer_array", and returns an array with 
% the same size than "buffer_array"

new_samples = size(new_data, 1);
new_buffer  = [data_buffer; new_data];
new_buffer(1:new_samples, :) = [];

