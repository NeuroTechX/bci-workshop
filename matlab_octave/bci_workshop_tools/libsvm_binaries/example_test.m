load('iris_dataset.mat');
irisInputs(:, 101:end, :) = [];
irisTargets(:, 101:end, :) = [];

X = irisInputs';
y = irisTargets(1,:)';

classifier = svmtrain(y, X);
irisHat = svmpredict(y(1), X(1,:), classifier);
