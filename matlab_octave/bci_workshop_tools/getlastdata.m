function new_buffer = getlastdata( data_buffer, newest_samples )
%UPDATEBUFFER:
% Obtains from "buffer_array" the "newest samples" (N rows from the bottom of the buffer)

new_buffer  = data_buffer( size(data_buffer,1) - newest_samples + 1 : end , :);

