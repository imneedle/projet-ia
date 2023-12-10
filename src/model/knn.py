#! /usr/bin/python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from sklearn.neighbors import KNeighborsRegressor


class KnnModel:
    def __init__(self, n_neighbors):
        self.n_neighbors = n_neighbors

    def train(self, df):
        y = df["aqi"]
        X = df.drop(["aqi"], axis=1)
        X.to_csv("X.csv")
        knn = KNeighborsRegressor(n_neighbors=self.n_neighbors)
        knn.fit(X, y)
        return knn
