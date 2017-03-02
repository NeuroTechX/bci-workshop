function plot_channels(data,fs,marker,labels,zero_mean)
%function plot_channels(data,fs,marker,labels,zero_mean)
%Several channels are ploted in the current Axes, Offset for vizualization is automaticly computed
%
% DATA        = [samples, channels], it will be plotted with zero mean
% FS          = Sampling frequency
% MARKER      = 1D array size [samples], only markers different to zero are
%               indicated
% LABELS      = Cell array with the name of the channels
% ZERO_MEAN   = If true, mean will removed from each column
%
% Raymundo Cassani

[samples, nElectrodes] = size(data);
time_units = true;

if nargin < 5
    zero_mean = false;
    if nargin <4
        labels = {};
        if nargin < 3
            marker = [];
            if nargin < 2
                fs = 1;
                time_units = false;
            end
        end
    end
end

% Retrieve Current Axes handle from the Current Figure
% If there is not Current Figure, a new figure is created
h_ax = get(gcf, 'CurrentAxes');

% If there is not Current Axes handle, create Axes in current Figure
if size(h_ax, 1) == 0
    h_ax = axes;
end

% Create time vector from number of samples and sampling frequency
timeV = (0:samples-1)/fs;

% Normalize data if requested
if zero_mean
    new_data = normalize_col(data);
else
    new_data = data;
end
    
% Calculate offset shift
min_ch = min(new_data);
min_ch(min_ch==0) = -1;
max_ch = max(new_data);
max_ch(max_ch==0) =  1;
offset_v = cumsum(abs(min_ch)) + [0, cumsum(abs(max_ch(1:end-1)))];

% Add offset to each channel in Data, and plot Data in the Current Axes
plot(h_ax, timeV,bsxfun(@plus,new_data,offset_v));

% Edit Y Axis to show Labels
set(h_ax,'ytick',offset_v,'yticklabel',labels);
set(h_ax,'XGrid','off','YGrid','on');
set(h_ax,'XMinorTick','on');
if ~time_units
    xlabel('Number of samples');
else
    xlabel('Time (s)');
end

% Color Array for markers
colorcell = {'k','b','g','r','y','m','c'};

% If Markers are present use vline to draw them
if numel(marker(marker ~= 0)) > 1
    vline(timeV(marker ~= 0), colorcell(mod(marker(marker ~= 0),numel(colorcell))+1), cellstr(num2str((marker(marker ~= 0)))));
elseif numel(marker(marker ~= 0)) == 1
    vline(timeV(marker ~= 0), colorcell{mod(marker(marker ~= 0),numel(colorcell))+1}, num2str((marker(marker ~= 0))));
end    
