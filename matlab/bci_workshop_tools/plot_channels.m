function plot_channels(h_axes, data, fs, labels)
%function plot_channels(h_axes, data, fs, labels)
%Several channels are ploted in the current Axes, Offset for vizualization is automaticly computed
%
% H_AXES      = Axes handle where the signals will be plotted
%               if empty i.e. '[]', a New figure with New Axes will be
%               created
% DATA        = [samples, channels], it will be plotted with zero mean
% FS          = Sampling frequency
% LABELS      = Cell array with the name of the channels

if ~exist('h_axes','var') || isempty(h_axes)
    % Retrieves Current Axes handle from the Current Figure
    % If there is not Current Figure, a new Figure is created
    h_axes = get(gcf, 'CurrentAxes');
end

[n_samples, n_channels] = size(data);

% Create time vector from number of samples and sampling frequency
time_vec = (0 : n_samples - 1) / fs;

% Offset 
y_max = 100;
ch_range = y_max / n_channels;
offset_v = ((0 : n_channels - 1) + 0.5) * ch_range;

% Normalize data to mean = 0, std = 1
new_data = normalize_col(data, 'mean_std');
new_data = new_data * ch_range / 5;

% Add offset to each channel in Data, and plot Data in the Current Axes
plot(h_axes, time_vec, bsxfun(@plus,new_data, offset_v));

% Edit Y Axis to show Labels
set(h_axes,'ytick',offset_v,'yticklabel',labels);
ylim(h_axes, [0, y_max ]);
% Axes grid and labels 
set(h_axes,'XGrid','off','YGrid','on');
set(h_axes,'XMinorTick','on');
xlabel(h_axes, 'Time (s)');

end
