function fig_closereq(src,callbackdata)
global stop_loop
% Figure close request function
% Changes the value of the global variable STOP_LOOP to True
% to display a question dialog box 
stop_loop = true;
delete(gcf);
end