import math
import numpy as np
import pandas as pd
from pandas import read_csv
from pandas.plotting import scatter_matrix
from matplotlib import pyplot
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn import preprocessing
import datetime


def show_info(df):
    print(df.shape)
    # print whole data frame
    # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    #     print(df)
    print(df.describe())
    # plots
    df.drop(['date', 'day'], 1).plot(kind='box', subplots=True, layout=(2, 2), sharex=False, sharey=False)
    pyplot.show()
    df.drop(['date', 'day'], 1).hist()
    pyplot.show()
    scatter_matrix(df.drop(['date'], 1))
    pyplot.show()


# not used
def add_prc_columns(series, names):
    for name in names[1:]:
        arr = np.zeros(len(series[name]))
        arr[0] = 1
        for i in range(1, len(arr)):
            if series[name][i - 1] == series[name][i]:
                arr[i] = 1
            elif series[name][i - 1] == 0:
                arr[i] = 2
            else:
                arr[i] = series[name][i] / series[name][i - 1]
        print(arr)
        series['prc_' + name] = arr


def prepare_data(df, names, num_prior_days):
    df['day'] = np.arange(len(df['date']))
    show_info(df)
    forecast_col = 'infected'
    for prev_day in range(1, num_prior_days + 1):
        for name in names[1:]:
            df['{}_prev{}'.format(name, prev_day)] = df[name].shift(prev_day, fill_value=0)
    df['label'] = df[forecast_col].shift(-1)
    X = np.array(df.drop(['day', 'date', 'label'], 1))
    X = preprocessing.scale(X)
    X_lately = X[-1:]
    X = X[:-1]
    y = np.array(df.dropna()['label'])
    return X, y, X_lately


def main():
    names = ['date', 'infected', 'cured', 'deaths']
    df = read_csv('data/data_20200514.csv', names=names)
    X, y, X_lately = prepare_data(df, names, 8)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    print('Train data size: {}'.format(len(X_train)))
    print('Test data size: {}'.format(len(X_test)))
    clf = LinearRegression()
    clf.fit(X_train, y_train)
    confidence = clf.score(X_test, y_test)
    print('Confidence: {}'.format(confidence))
    forecast_set = clf.predict(X_lately)
    next_date = datetime.datetime.strptime(str(int(df.iloc[-1]['date'])), '%Y%m%d') + datetime.timedelta(days=1)
    print('Forecast for date {}: {} infected ({} rounded)'.format(next_date.strftime('%Y/%m/%d'), forecast_set[0],
                                                                  int(forecast_set[0] + 0.5)))


if __name__ == '__main__':
    main()
