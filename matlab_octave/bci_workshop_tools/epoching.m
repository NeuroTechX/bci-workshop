function [epochs, remainder, ix_center] = epoching(data,size_epoch,overlap_epoch)
% [EPOCHS, REMAINDER, IX_CENTER] = EPOCHING( DATA, SIZE_EPOCH, OVERLAP)
% Divides the DATA provided as [n_samples, n_channels] using the 
% SIZE_EPOCH indicated (in samples) and the OVERLAP between consecutive
% epochs.
% 
% EPOCHS     has the shape [n_samples, n_channels, n_epochs]
%            where:
%            n_epochs = floor( (n_samples - size_epoch) / shift_epoch ) + 1 ;
%
% REMAINDER  has the shape [n_samples, n_channels], contains samples from
%            DATA that are located after the last complete EPOCH
%
% IX_CENTER  has the shape [n_epochs, 1]
%            it indicates the index tha corresponds to the center of the
%            nth epoch. If the epoch has an even number of elements, this
%            index is CEIL()
% 
%
%
% e.g 
% size_epoch = 5 overlap = empty
%
%  n_epochs = floor(n_samples / size_epoch) = floor (23 / 5) = 4
%   1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3       (Data array)
%  |E1       |E2       |E3       |E4       |Remainder
%       *         *         *         *                 (* = center of the epoch)      
% ix_center =  [3, 8, 13, 18]
%
% e.g 
% size_epoch = 5  and overlap_epoch = 2
% shift_epoch = size_epoch - overlap_epoch 
%
% n_epochs = floor( (n_samples - size_epoch) / shift_epoch ) + 1 ;
% n_epochs = floor( (24 - 5) / 3 ) + 1  = 7
% 
%  1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4       (Data array)
% |E1-------| |E3-------| |E5-------| |E7-------|
%       |E2-------| |E4-------| |E6-------|     |R| 
%      *           *           *           *           
%            *           *           *                   (* = center of the epoch) 
% ix_center = [3, 6, 9, 12, 15, 18, 21]
% remainder = [4]
% Raymundo Cassani
%

% Verify the number of Input arguments
if nargin < 3
    overlap_epoch = 0;
end

% Obtain parameters of the data
n_samples = size(data,1);
n_channels = size(data,2);

% Size of half epoch
half_epoch = floor(size_epoch / 2);

% Epoch shift
shift_epoch = size_epoch - overlap_epoch;

% Number of epochs
n_epochs = floor( (n_samples - size_epoch) / shift_epoch ) + 1 ;

%markers indicates where the epoch starts, and the epoch contains 
%size_epoch elements

markers = ((1:n_epochs)'*shift_epoch)+1;
markers = [1; markers];

%Divide data in epochs
epochs = zeros(size_epoch,n_channels,n_epochs);
ix_center = zeros(n_epochs,1);

for i_epoch = 1:n_epochs
    epochs(:,:,i_epoch) = data( markers(i_epoch) : markers(i_epoch) + size_epoch -1 ,:);
    ix_center(i_epoch) = markers(i_epoch) - 1 + half_epoch;
end

if (markers(end)~= n_samples) 
    remainder = data(markers(end-1) + size_epoch : n_samples,:);
else
    remainder = [];
end