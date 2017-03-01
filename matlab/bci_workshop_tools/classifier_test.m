function [ y_hat ] = classifier_test( classifier, feature_vector, mu_ft, std_ft )
%CLASSIFIER_TEST 
% Test the classifier on new data points.
% 
% Arguments
% classifier: trained classifier (scikit object)
% feature_vector: np.array of shape [number of feature points; number of different features]
% mu_ft, std_ft: normalization parameters for the data
% 
% Output
% y_hat: decision of the classifier on the data points

% Normalize feature_vector
x = (feature_vector - mu_ft) ./ std_ft;    
y_hat = svmclassify(classifier, x);

end

