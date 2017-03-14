function [ feature_matrix ] = compute_feature_matrix( epochs, Fs )
%COMPUTE_FEATURE_MATRIX 
% Call compute_feature_vector for each EEG epoch contained in the "epochs"

n_epochs = size(epochs, 3);

for i_epoch = 1 : n_epochs
    if i_epoch == 1
        feat = compute_feature_vector(epochs(:, :, i_epoch), Fs);
        feature_matrix = zeros(n_epochs, numel(feat)); % Initialize feature_matrix
    end
    feature_matrix(i_epoch, :) = compute_feature_vector(epochs(:, :, i_epoch), Fs);   
end

end

