function [classifier, mu_ft, std_ft] = classifier_train( feature_matrix_0, feature_matrix_1, algorithm )
%CLASSIFIER_TRAIN 
% Trains a binary classifier using the SVM algorithm with the following parameters
% 
% Arguments
% feature_matrix_0: Matrix with examples for Class 0
% feature_matrix_0: Matrix with examples for Class 1
% algorithm: Currently only SVM is supported
% 
% Outputs
% classfier: trained classifier (scikit object)
% mu_ft, std_ft: normalization parameters for the data

% Create vector Y (class labels)
class0 = zeros(size(feature_matrix_0,1),1); 
class1 = ones(size(feature_matrix_0,1),1); 
    
% Concatenate feature matrices and their respective labels
y = [class0; class1];
features_all = [feature_matrix_0; feature_matrix_1];
    
% Normalize features, columnwise
mu_ft = mean(features_all, 1);
std_ft = std(features_all, 1);

X_tmp = bsxfun(@minus, features_all, mu_ft);
X = bsxfun(@rdivide, X_tmp, std_ft);

% Train SVM, using default parameters     
classifier = svmtrain(y , X, '-q');

end

