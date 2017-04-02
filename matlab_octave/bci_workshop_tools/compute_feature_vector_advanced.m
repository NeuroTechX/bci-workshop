function feature_vector = compute_feature_vector_advanced( eegdata, Fs )
%COMPUTE_FEATURE_VECTOR ADVANCED
% Extract the features from the EEG
% 
% Arguments:
% eegdata: array of dimension [number of samples, number of channels]
% Fs: sampling frequency of eegdata
% 
% Outputs:
% feature_vector: np.array of shape [number of feature points; number of different features]

% Delete last column (Status)
X = eegdata(:, 1: end - 1);

% 1. Compute the PSD
[winSampleLength, nbCh] = size(X);

% Apply Hamming window
w = repmat(hanning(winSampleLength), [1, nbCh]);
dataWinCentered = bsxfun(@minus,X,mean(X));
dataWinCenteredHam = dataWinCentered .* w;

NFFT = nextpow2(winSampleLength);
Y = fft(dataWinCenteredHam, NFFT, 1) ./ winSampleLength;
PSD = 2 * abs(Y ( 1 : NFFT/2, : ) );
f =  (Fs / 2) * linspace(0, 1, NFFT/2);

% SPECTRAL FEATURES
% Average of band powers
% Delta <4
ind_delta = f < 4;
meanDelta = mean(PSD(ind_delta,:), 1);
% Theta 4-8
ind_theta = ((f>=4) & (f<=8));
meanTheta = mean(PSD(ind_theta,:), 1);
% Low Alpha 8-10
ind_alpha = ((f>=8) & (f<=10)); 
meanLowAlpha = mean(PSD(ind_alpha,:), 1);
% Medium Alpha 9-11
ind_alpha = ((f>=9) & (f<=11)); 
meanMedAlpha = mean(PSD(ind_alpha,:), 1);
% High Alpha 10-12
ind_alpha = ((f>=10) & (f<=12)); 
meanHighAlpha = mean(PSD(ind_alpha,:), 1);
% Low Beta 12-21
ind_beta = ((f>=12) & (f<21));
meanLowBeta = mean(PSD(ind_beta,:), 1);
% HighBeta 21-30
ind_beta = ((f>=21) & (f<30));
meanHighBeta = mean(PSD(ind_beta,:), 1);
% Alpha 8-12
ind_alpha = ((f>=8) & (f<=12)); 
meanAlpha = mean(PSD(ind_alpha,:), 1);
% Beta 12-30
ind_beta = ((f>=12) & (f<30));
meanBeta = mean(PSD(ind_beta,:), 1);

feature_vector = [meanDelta, meanTheta, meanLowAlpha, meanHighAlpha, ...
                  meanLowBeta, meanHighBeta, ...
                  meanDelta ./ meanBeta, meanTheta ./ meanBeta, ...
                  meanAlpha ./ meanBeta, meanAlpha ./ meanTheta ];

feature_vector = log10(feature_vector);
end


function n = nextpow2(i)
% Find the next power of 2 for number i
    n =1;
    while n < i
        n = n * 2;
    end
end


