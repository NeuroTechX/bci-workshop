function [X_norm, mu, sigma] = normalize_col(X, kind)
%[X_NORM, mu, sigma] =  NORMALIZE_COL(X, kind);
%Normalizes the features in X;  'mean' and 'mean_std' options
%
%   NORMALIZE(X) or NORMALIZE(X,'mean') returns a normalized version of X 
%   (X_NORM), where the mean value of each feature (column) is 0 
%
%   NORMALIZE(X,'mean_std') returns a normalized version of X (X_NORM), where
%   the mean value of each feature (column) is 0 and the 
%   standard deviation is 1. 
%
%   Variables MU and SIGMA contain the mean and standard deviation
%   columnwise

% Raymundo Cassani

if nargin < 2
    kind = 'mean';
end

%Initialize variables
X_norm = X;
mu = zeros(1, size(X, 2));
sigma = zeros(1, size(X, 2));

mu = mean(X);
sigma = std(X);

% In case std is 0, make std = 1; 
sigma(sigma == 0) = 1;


X_norm = bsxfun(@minus,X,mu);
if strcmp(kind,'mean')
    return
    elseif strcmp(kind,'mean_std')
        X_norm = bsxfun(@rdivide, X_norm,sigma);
    return
end
end

