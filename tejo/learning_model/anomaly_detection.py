import numpy as np
import pylab as pl
import matplotlib
import datetime as dt
#import matplotlib.font_manager
#from scipy import stats

from sklearn import svm, grid_search, metrics, preprocessing
#from sklearn.covariance import EllipticEnvelope

import sys

from numpy import genfromtxt

from time import gmtime, strftime

DEFAULT_CACHE_SIZE=3000

class OneClassSVMClassifier:
    """
    generic SVM classifier for binary classification (1/-1)
    with default parameters

    """

    def __init__(self,training_data, nu=0.05, kernel="rbf", gamma=0.1, degree=3, shrinking=True,cache_size=DEFAULT_CACHE_SIZE):
        """
        it requires a tab-separated training data containing
        common (unpopular/normal) data

        the classifier is then ready to identify outliers
        or anomalies
        """
        my_data = genfromtxt(training_data, delimiter='\t',skip_header=0)

        #preprocessing data
        X = preprocessing.scale(my_data)

        #defining scaling
        self.scaler = preprocessing.StandardScaler()
        self.scaler.fit(my_data)

        #define classifier
        self.classifier = svm.OneClassSVM(nu=nu, kernel=kernel, gamma=gamma, degree=degree, shrinking=shrinking,cache_size=cache_size)
        self.classifier.fit(X)

    def scale(self,X):
        return self.scaler.transform(X)

    def predict(self,X):
        """
        raw predictions from sklearn library
        it assumes that inputs have already been
        set to the correct scale
        """
        return self.classifier.predict(X) 