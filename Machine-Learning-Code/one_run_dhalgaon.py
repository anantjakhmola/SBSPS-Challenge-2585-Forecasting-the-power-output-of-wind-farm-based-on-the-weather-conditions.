# -*- coding: utf-8 -*-
"""one_run_Dhalgaon.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1byj2TfFQgXm9QoX71PWpdjSr6fSKYkpt
"""

# -*- coding: utf-8 -*-
"""one_run_Dhalgaon.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1z--_QfnN-W5RgCaus4mbT66X-4RZvjhP
"""

#! pip install tbats
#! pip install mxnet
#! pip install nbeats_forecast

from datetime import datetime, timedelta
from dateutil import tz
import requests
import json
import time
import gc

import pandas as pd
import numpy as np

import seaborn as sns
from matplotlib import pyplot as plt

from sklearn.metrics import mean_squared_error
from sklearn.linear_model import LinearRegression, SGDRegressor, BayesianRidge
from sklearn.preprocessing import PolynomialFeatures, MinMaxScaler
from sklearn.model_selection import RandomizedSearchCV
from sklearn.ensemble import StackingRegressor

import xgboost as xgb
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor
from hyperopt import hp, fmin,tpe,Trials, STATUS_OK


import keras
from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout, Bidirectional, Flatten, BatchNormalization
from keras.optimizers import Adam
from torch import optim

start_time = datetime.now()
print("Starting Time of Scrip: ",start_time)  # Start Time

import warnings
warnings.filterwarnings("ignore")

# FETCH THE REMAINING
API_KEY = '8a7a5c90b0d94dca908583248bc49929'

def fetch_current():

  list_of_frames = []

  to_zone = tz.gettz('Asia/Kolkata')
  utc = datetime.now()
  central = utc.astimezone(to_zone)

  # DATES TO FETCH
  N=1
  current_date = central.date() + timedelta(days=1)
  for i in range(0,1):                          # ****** MAIN FOR-LOOP *******
    
      current_date = current_date - timedelta(days=N)
      past_day = current_date - timedelta(days=N)
      print(current_date,past_day)


      #                 ************** WEATHER_BIT API CONNECTION ***************
    
      API_KEY = '8a7a5c90b0d94dca908583248bc49929'

      url = f"https://api.weatherbit.io/v2.0/history/hourly?lat=17.14&lon=74.95&start_date={past_day}&end_date={current_date}&tz=local&key={API_KEY}"
      response = requests.get(url)

      print(response.status_code)
      weather = json.loads(response.text)  
      time.sleep(1)  
    
      #                 *************** CONVERSION TO DATAFRAME ****************
    
    
 
      df_current = pd.DataFrame.from_dict(weather['data'][0],orient='index').transpose()
      for forecast in weather['data'][1:]:
          df_current = pd.concat([df_current, pd.DataFrame.from_dict(forecast,orient='index').transpose()])
 
    # extract time and use it as index
      time_ = np.array(df_current['timestamp_local'])
      for row in range(len(time_)):
          time_[row] = datetime.strptime(time_[row], '%Y-%m-%dT%H:%M:%S')
 
      df_current = df_current.set_index(time_)
        
    
      #                 ********* ACCUMULATING ALL DATA IN A SINGLE FRAME ********
    
      list_of_frames.append(df_current)

#del df
#gc.collect()
  print("Fetch completed...!!!  :)")
  df_current = pd.concat(list_of_frames)
  df_current = df_current.sort_index()
  df_current.shape    
  df_full = df_current.copy()

  return df_current

def decode_weather(df_):
  icon = []
  code = []
  des  = []
  for i in df_['weather']:
    icon.append(i['icon'])
    code.append(i['code'])
    des.append(i['description'])

  df_['Icon'] = icon
  df_['Code'] = code
  df_['Description'] = des

  del icon,code,des
  gc.collect()
  df_.drop(['snow','ts','weather','timestamp_utc','timestamp_local','datetime'],axis=1,inplace=True)
  return df_
df_current = fetch_current()
df_current = decode_weather(df_current)

def format_dataframe(df):
  df.index = pd.to_datetime(df.index)
  if "Energy" in df.columns:
    pass
  else:
    col_names = ['Humidity','Wind_Speed','Visibility','Sea_level_pres','day/night','Normal_irradiance','Solar_Elevation','Pressure','Solar_hour_angle',
             'Dew_Point','UV_index','Solar_Rad','Wind_Direction','Global_irradiance','Direct_irradiance','Avg_temp','Azi_anlge',
             'Temperature','Precipitation','Clouds','Icon','Code','Description']
    df.columns = col_names
    df.drop(['Solar_Elevation', 'Azi_anlge', 'Solar_hour_angle'],axis=1,inplace=True)
    df['Energy'] = ((0.5 * 1.23 * (3.14 * 40 *40 ) * (df['Wind_Speed']**3)  * 0.28) * 1)/1000

  df[['Humidity','Wind_Speed','Visibility','Sea_level_pres','Normal_irradiance','Pressure','Dew_Point','UV_index','Solar_Rad',
             'Wind_Direction','Global_irradiance','Direct_irradiance','Avg_temp','Temperature','Precipitation','Clouds','Code',
             'Energy']] = df[['Humidity','Wind_Speed','Visibility','Sea_level_pres','Normal_irradiance','Pressure',
             'Dew_Point','UV_index','Solar_Rad','Wind_Direction','Global_irradiance','Direct_irradiance','Avg_temp',
             'Temperature','Precipitation','Clouds','Code','Energy']].apply(pd.to_numeric)
  df.asfreq(freq='H')
  return df

df_current = format_dataframe(df_current)
#df_current.head(1)

# Historical DATA
df_prev = pd.read_csv("/home/ubuntu/files/Dhalgaon.csv",index_col=[0])
list_drop=['Solar_Elevation','Solar_hour_angle','Azi_anlge']
for i in list_drop:
  if i in df_prev.columns:
    df_prev.drop([i],axis=1,inplace=True) 
df_prev = format_dataframe(df_prev)
df_prev.to_period('H')
df_prev.tail(2)

# Future Fetch
url = f"https://api.weatherbit.io/v2.0/forecast/hourly?lat=17.14&lon=74.95&key={API_KEY}&hours=120"

response = requests.get(url)

print(response.status_code)
weather = json.loads(response.text) 


df_future = pd.DataFrame.from_dict(weather['data'][0],orient='index').transpose()
for forecast in weather['data'][1:]:
    df_future = pd.concat([df_future, pd.DataFrame.from_dict(forecast,orient='index').transpose()])
 
# extract time and use it as index
time_ = np.array(df_future['timestamp_local'])
for row in range(len(time_)):
    time_[row] = datetime.strptime(time_[row], '%Y-%m-%dT%H:%M:%S')
 
df_future = df_future.set_index(time_)
df_future.index = pd.to_datetime(df_future.index)
df_future = decode_weather(df_future)
df_future.to_csv("Dhalgaon_future.csv")

df_jsons = pd.DataFrame()
df_jsons = df_future[['wind_spd','uv']]
df_jsons.drop(['uv'],axis=1,inplace=True)     
df_jsons.index = df_future.index
df_jsons.index = pd.to_datetime(df_jsons.index)
df_jsons.index = df_jsons.index.astype('string')
df_jsons = df_jsons.T
df_jsons.to_json('Dhalgaon_Wind_48hrs.json', orient='records')

df_feature_json = df_future[['rh','pres','temp','precip','uv','ozone','pop','clouds']]
cols_temp = ['Humidity','Pressure','Temperature','Precipitation','UV Index','Ozone','Rain_Probability','Clouds']
df_feature_json.columns = cols_temp
df_feature_json[['Humidity','Pressure','Temperature','Precipitation','UV Index','Ozone','Rain_Probability','Clouds']]= df_feature_json[['Humidity','Pressure','Temperature','Precipitation','UV Index','Ozone','Rain_Probability','Clouds']].apply(pd.to_numeric)
df_feature_json.index =pd.to_datetime(df_feature_json.index)

double_df = pd.DataFrame()
name = []
value = []
for i in df_feature_json.columns:
  name.append(str(i)+"_today")
  name.append(str(i)+"_tomorrow")
  value.append(np.mean(df_feature_json[str(i)][:24].values))
  value.append(np.mean(df_feature_json[str(i)][24:].values))
  
double_df['names'] = name
double_df['values'] = value  
double_df.index = double_df['names']
double_df.drop(['names'],axis=1,inplace=True)
double_df = double_df.T
double_df.to_json('Dhalgaon_Features_2_days.json', orient='records')


df_future = df_future[['rh','wind_spd','vis','slp','pod','dni','pres','dewpt','uv','solar_rad',
                       'wind_dir','ghi','dhi','app_temp','temp','precip','clouds','Icon','Code','Description']]

col_name_future = ['Humidity','Wind_Speed','Visibility','Sea_level_pres','day/night','Normal_irradiance','Pressure',
             'Dew_Point','UV_index','Solar_Rad','Wind_Direction','Global_irradiance','Direct_irradiance','Avg_temp',
             'Temperature','Precipitation','Clouds','Icon','Code','Description']
df_future.columns = col_name_future
df_future['Energy'] = ((0.5 * 1.23 * (3.14 * 40 *40 ) * (df_future['Wind_Speed']**3)  * 0.28) * 1)/1000
df_future[['Humidity','Wind_Speed','Visibility','Sea_level_pres','Normal_irradiance','Pressure','Dew_Point','UV_index',
            'Solar_Rad','Wind_Direction','Global_irradiance','Direct_irradiance','Avg_temp','Temperature',
            'Precipitation','Clouds','Code','Energy']] = df_future[['Humidity','Wind_Speed','Visibility','Sea_level_pres',
            'Normal_irradiance','Pressure','Dew_Point','UV_index','Solar_Rad','Wind_Direction','Global_irradiance',
            'Direct_irradiance','Avg_temp','Temperature','Precipitation','Clouds','Code','Energy']].apply(pd.to_numeric)



# Concatenating the DataFrames

temp_list = []
temp_list.append(df_prev)
temp_list.append(df_current)
df = pd.concat(temp_list)
df = df.sort_index()
df.to_csv("Dhalgaon.csv")

del temp_list
gc.collect

temp_list_2 =[]
temp_list_2.append(df)
temp_list_2.append(df_future)
df = pd.concat(temp_list_2)
df = df.sort_index()

del temp_list_2
gc.collect()

df.shape

#for i in df.columns:
#  print((df[str(i)].isnull().sum()))
for i in df.columns:
  if df[str(i)].isnull().sum()>0:
    df[str(i)] = df[str(i)].fillna(df[str(i)].mean())

# helper for mean_encoding
def mean_encoding(col_to_encode,target,new_name):
  encode = df.groupby(col_to_encode)[target].mean()
  df.loc[:,new_name] = df[col_to_encode].map(encode)

# Adding "Month" as a feature and applying target mean encoding to it
df['Month'] = pd.DatetimeIndex(df.index).month
encod_month = df.groupby('Month')['Energy'].mean()
df.loc[:, 'month_mean_enc'] = df['Month'].map(encod_month)
#df[['Month','month_mean_enc']].head()

# More Date related Features
df['quarter'] = pd.DatetimeIndex(df.index).quarter
df['week_of_year'] = pd.DatetimeIndex(df.index).weekofyear
df['day_of_week'] = pd.DatetimeIndex(df.index).dayofweek
df['day_of_month'] = pd.DatetimeIndex(df.index).day
df['hour_of_day'] = pd.DatetimeIndex(df.index).hour
df.columns

# Convertin wind direction into text format [East, West, North, South]
def wind_direction_text(num):
  val=int((num/22.5)+.5)
  arr=["N","NNE","NE","ENE","E","ESE", "SE", "SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
  return arr[(val % 16)]

# Direction is a categorical feature so to make use of it in forecasting using ML predictor we use target encoding
df['Direction']  = df['Wind_Direction'].apply(wind_direction_text)

# Apllying Lag Based Features
df['lag_1'] = df['Energy'].shift(1)
df['lag_2'] = df['Energy'].shift(2)
df['lag_3'] = df['Energy'].shift(3)
df['lag_12'] =  df['Energy'].shift(12)
# applying rolling mean as Power generated at point will somehow depend on previous performance
df['rolling_mean_1'] = df['Energy'].rolling(window=1).mean()
df['rolling_mean_2'] = df['Energy'].rolling(window=2).mean()
df['rolling_mean_3'] = df['Energy'].rolling(window=3).mean()
df['rolling_mean_6'] = df['Energy'].rolling(window=6).mean()

# MORE ROLLING FEATURES 
for i in [36,72,144]:
    print('Rolling period:', i)
    df['rolling_mean_'+str(i)] = df['Energy'].transform(lambda x: x.shift(1).rolling(i).mean())
    df['rolling_std_'+str(i)]  = df['Energy'].transform(lambda x: x.shift(1).rolling(i).std())

cat_cols = list(df.select_dtypes(include=['object']).columns) 
num_cols = list(df.select_dtypes(exclude=['object']).columns)
print("cat cols:",cat_cols)
print("numeric cols:",num_cols)

train_bound = df.shape[0] - (48*3)
val_bound = df.shape[0]-(48*1)
XGB_df = df.copy()
XGB_df.shape

from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error


XGB_df.drop(['day/night', 'Icon', 'Description', 'Direction'],axis=1,inplace=True)  # Dropping the Categorical Columns

# Trainig / Dev (Cross Validation) / Test Split  (LINEAR SPLIT ONLY)
XGB_X_train = XGB_df[:train_bound]
XGB_X_cv = XGB_df[train_bound:val_bound]
XGB_X_test = XGB_df[-48:]
XGB_Y_train = XGB_X_train['Energy']
XGB_Y_cv = XGB_X_cv['Energy']
XGB_Y_test = XGB_X_test['Energy']

XGB_X_train.drop(['Energy'],axis=1,inplace=True)
XGB_X_cv.drop(['Energy'],axis=1,inplace=True)
XGB_X_test.drop(['Energy'],axis=1,inplace=True)

#  Bayesian optimization for parameter tuning using HYPEROPT

from hyperopt import hp, fmin,tpe,Trials, STATUS_OK

def XGB_fine_tune(space):
  XGB_model = XGBRegressor(n_estimators =1000,
                           learning_rate = space['learning_rate'],
                           colsample_bytree=space['colsample_bytree'],
                           max_depth = space['max_depth'],
                           num_leaves = space['num_leaves'],
                           min_child_weight = space['min_child_weight'],
                           feature_fraction = space['feature_fraction'],
                           bagging_fraction = space['bagging_fraction'],
                           subsample = space['subsample'],
                           gamma = space['gamma'],
                           reg_lambda = space['reg_lambda'],
                           )
  eval_set = [(XGB_X_train,XGB_Y_train),(XGB_X_cv,XGB_Y_cv)]

  XGB_model.fit(XGB_X_train, XGB_Y_train,
            eval_set=eval_set, eval_metric="rmse",
            early_stopping_rounds=10,verbose=1)
  
  XGB_predictions = XGB_model.predict(XGB_X_cv)

  XGB_rmse= np.sqrt(mean_squared_error(XGB_predictions,XGB_Y_cv))

  return {'loss':XGB_rmse, 'status':STATUS_OK}

print(" \n\nBest Model Search processing for XgBoost...")
space ={'learning_rate':hp.loguniform('learning_rate',np.log(0.01), np.log(0.5)),
        'max_depth': hp.choice("x_max_depth",range( 4, 16, 1)),
        'num_leaves': hp.choice('num_leaves', range(2, 300, 1)),
        'min_child_weight': hp.quniform ('x_min_child', 1, 10, 1),
        'feature_fraction': hp.uniform('feature_fraction', 0.1, 1.0),
        'bagging_fraction': hp.uniform('bagging_fraction', 0.1, 1.0),
        'subsample': hp.uniform('subsample', 0.1, 1.0),
        'gamma' : hp.uniform ('x_gamma', 0.1,0.5),
        'colsample_bytree' : hp.uniform ('x_colsample_bytree', 0.7,1),
        'reg_lambda': hp.uniform ('x_reg_lambda', 0,1),
        
    }
trials = Trials()
best = fmin(fn=XGB_fine_tune,
            space=space,
            algo=tpe.suggest,
            max_evals=10,
            trials=trials)
print("BEST PARAMETERS:",best)

# FITTING MODEL WITH HYPERPARAMETERS OBTAINED AFTER AUTOMATIC TUNING
xgb_ft_model =XGBRegressor(n_estimators =1000,
                           boosting_type='gbdt',
                           learning_rate = best['learning_rate'],
                           colsample_bytree= best['x_colsample_bytree'],
                           max_depth = best['x_max_depth'],
                           metric='rmse',
                           num_leaves = best['num_leaves'],
                           min_child_weight = best['x_min_child'],
                           feature_fraction = best['feature_fraction'],
                           bagging_fraction = best['bagging_fraction'],
                           subsample = best['subsample'],
                           gamma = best['x_gamma'],
                           random_state=222,
                           #reg_alpha=0.3899,
                           reg_lambda = best['x_reg_lambda'],
                           verbosity=1
                           
                           )
eval_set = [(XGB_X_train,XGB_Y_train),(XGB_X_cv,XGB_Y_cv)]

xgb_ft_model.fit(XGB_X_train, XGB_Y_train,
          eval_set=eval_set, eval_metric="rmse",early_stopping_rounds=10,verbose=1)

xgb_ft_predictions = xgb_ft_model.predict(XGB_X_test)

xgb_ft_rmse= np.sqrt(mean_squared_error(xgb_ft_predictions,XGB_Y_test))
print("XGBoost's Score:",xgb_ft_rmse)
XGB_result = pd.DataFrame()
XGB_result['Theoretical'] = XGB_Y_test
XGB_result['Predictions'] = xgb_ft_predictions

'''
plt.figure(figsize=(20,8))
plt.plot(XGB_result)
plt.title("XGboost's Performance")
plt.xlabel("Time Stamps")
plt.ylabel("Active Power")
plt.legend(loc="upper left")
plt.show()
'''

'''
import xgboost as xgb
fig, ax = plt.subplots(figsize=(12,10))
xgb.plot_importance(xgb_ft_model, max_num_features=50, height=0.5, ax=ax)
ax.grid(False)
plt.title("XGB - Feature Importance", fontsize=15)
plt.show()
'''

from lightgbm import LGBMRegressor
from sklearn.metrics import mean_squared_error


LGBM_df = df.copy()

LGBM_df.drop(['day/night', 'Icon', 'Description', 'Direction'],axis=1,inplace=True)  # Removing categorical
LGBM_X_train = LGBM_df[:train_bound]
LGBM_X_cv = LGBM_df[train_bound:val_bound]
LGBM_X_test =  LGBM_df[-48:]

LGBM_Y_train = LGBM_X_train['Energy']   # Training Labels
LGBM_Y_cv = LGBM_X_cv['Energy']
LGBM_Y_test = LGBM_X_test['Energy']         # Cross Validation Labels

LGBM_X_train.drop(['Energy'],axis=1,inplace=True)
LGBM_X_cv.drop(['Energy'],axis=1,inplace=True)
LGBM_X_test.drop(['Energy'],axis=1,inplace=True)

# dimension check
print("Trains:", LGBM_X_train.shape, LGBM_Y_train.shape)
print("Validation:",LGBM_X_cv.shape, LGBM_Y_cv.shape)
print("Tests:",LGBM_X_test.shape, LGBM_Y_test.shape)
time.sleep(4)

from hyperopt import hp, fmin,tpe,Trials, STATUS_OK

def LGBM_fine_tune(space):
  LGBM_model = LGBMRegressor(metric='rmse',
                           n_estimators = 1024,
                           num_leaves = space['num_leaves'],
                           min_child_weight = space['min_child_weight'],
                           subsample= space['subsample'],
                           colsample_bytree = space['colsample_bytree'], 
                           feature_fraction=space['feature_fraction'],
                           bagging_fraction = space['bagging_fraction'],
                           min_data_in_leaf = 128,
                           learning_rate =space['learning_rate'],
                           max_depth =space['max_depth'],
                           max_bin = space['max_bin'],
                           reg_alpha=space['reg_alpha'],
                           reg_lambda=space['reg_lambda'],
                           gamma = space['gamma'],
                           random_state=222)
  
  eval_set = [(LGBM_X_train,LGBM_Y_train),(LGBM_X_cv,LGBM_Y_cv)]

  LGBM_model.fit(LGBM_X_train, LGBM_Y_train,
            eval_set=eval_set, eval_metric="rmse",
            early_stopping_rounds=10,verbose=1)
  
  LGBM_predictions = LGBM_model.predict(LGBM_X_cv)

  LGBM_rmse= np.sqrt(mean_squared_error(LGBM_predictions,LGBM_Y_cv))

  return {'loss':LGBM_rmse, 'status':STATUS_OK}

# SEARCH SPACE FOR LIGHT-GBM PARAMETERS
print("\n\n Searching Best model search for Light GBM...")
space = { 'max_depth' : hp.choice('max_depth', range(0, 16, 1)),
            'num_leaves': hp.choice('num_leaves',range(32,512,16)),
            'feature_fraction': hp.uniform('feature_fraction',0.2,1.0),
            'bagging_fraction':hp.uniform('bagging_fraction',0.2,1.0),
            'learning_rate' : hp.loguniform('learning_rate', np.log(0.01), np.log(0.5)),
            #'n_estimators' : hp.choice('n_estimators', range(128, 1024, 64)),
            'gamma' : hp.uniform('gamma', 0.1, 0.50),
            'min_data_in_leaf':hp.randint('min_data_in_leaf',range(64,256)),
            'max_bin' : hp.choice('max_bin',range(32,512,32)),
            'min_child_weight' : hp.quniform('min_child_weight', 1, 15, 1),
            'subsample' : hp.uniform('subsample', 0.1, 1.0),
            'reg_alpha': hp.uniform('reg_alpha', 0.0, 1.0),
            'reg_lambda': hp.uniform('reg_lambda', 0.0, 1.0),
            'colsample_bytree' : hp.uniform('colsample_bytree', 0.5, 1.0)
            }
trials = Trials()
best_ = fmin(fn=LGBM_fine_tune,
            space=space,
            algo=tpe.suggest,
            max_evals=20,
            trials=trials)
print("BEST PARAMETERS:",best_)
# DONE

# FITTING MODEL WITH HYPERPARAMETERS OBTAINED AFTER AUTOMATIC TUNING
#import lightgbm as lgb
lgbm_ft_model = LGBMRegressor(boosting_type='gbdt', 
                           metric='mape',
                           n_estimators = 512,
                           num_leaves = best_['num_leaves'],
                           min_child_weight = best_['min_child_weight'],
                           subsample = best_['subsample'],
                           colsample_bytree = best_['colsample_bytree'], 
                           feature_fraction = best_['feature_fraction'],
                           bagging_fraction = best_['bagging_fraction'],
                           min_data_in_leaf = 128,
                           learning_rate = best_['learning_rate'],
                           max_depth = best_['max_depth'],
                           max_bin = best_['max_bin'],
                           reg_alpha = best_['reg_alpha'],
                           reg_lambda = best_['reg_lambda'],
                           gamma = best_['gamma'],
                           random_state=222)


eval_set = [(LGBM_X_train,LGBM_Y_train),(LGBM_X_cv,LGBM_Y_cv)]

lgbm_ft_model.fit(LGBM_X_train, LGBM_Y_train,
          eval_set=eval_set, eval_metric="rmse",early_stopping_rounds=10,verbose=1)

lgbm_ft_predictions = lgbm_ft_model.predict(LGBM_X_test)

lgbm_ft_rmse= np.sqrt(mean_squared_error(lgbm_ft_predictions,LGBM_Y_test))
print("Light GBM's Score:",lgbm_ft_rmse)
#RESULTS['Light GBM'] = lgbm_ft_predictions
'''
from tbats import TBATS, BATS

print("\n\nTraining T-BATS ...")

train = df['Energy'][:val_bound]
test = df['Energy'][-48:].values

estimator = TBATS(seasonal_periods=(12,24))
model = estimator.fit(train)
TBATS_forecast = model.forecast(steps=48)
print("TBats Performace",np.sqrt(mean_squared_error(TBATS_forecast,test)))

#pip freeze > requirements.txt
'''
"""**IMPLEMENTING LSTM (if they could help)**"""
'''
from sklearn.preprocessing import MinMaxScaler
import keras
from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout, Bidirectional, Flatten, BatchNormalization
from keras.optimizers import Adam
from sklearn.metrics import mean_squared_error

def plot_predictions(test,predicted):
    plt.figure(figsize=(18,6))
    plt.plot(test, color='red',label='Real Energy Production')
    plt.plot(predicted, color='blue',label='Predicted Energy Production')
    plt.title('Wind Energy Prediction')
    plt.xlabel('Time')
    plt.ylabel('Energy')
    plt.legend()
    plt.show()

LSTM_df = df.copy()
lstm_bound = LSTM_df.shape[0]-96
training_set = LSTM_df['Energy'][:lstm_bound].values
training_set = np.reshape(training_set,(-1,1))
test_set = LSTM_df['Energy'][-96:].values

sc = MinMaxScaler(feature_range=(0,1))
training_set_scaled = sc.fit_transform(training_set)
X_train=[]
y_train=[]
for i in range(48,len(training_set)):
    X_train.append(training_set_scaled[i-48:i,0])
    y_train.append(training_set_scaled[i,0])
X_train, y_train = np.array(X_train), np.array(y_train)

X_train = np.reshape(X_train, (X_train.shape[0],X_train.shape[1],1))
#X_train.shape[1]

# LSTM architecture

model = Sequential()

model.add(Bidirectional(LSTM(units=128, return_sequences=True, input_shape=(X_train.shape[1],1))))
model.add(Dropout(0.2))

model.add(Bidirectional(LSTM(units=128, return_sequences=True)))
model.add(BatchNormalization())
model.add(Dropout(0.2))

model.add(Bidirectional(LSTM(units=64, return_sequences=True)))
model.add(Dropout(0.2))

model.add(Bidirectional(LSTM(units=64, return_sequences=True)))
model.add(BatchNormalization())
model.add(Dropout(0.2))

model.add(Flatten())
model.add(Dense(units=1))

model.compile( optimizer='adam', loss='mse')

# Fitting the Model
print("Fitting Neural Network....")
model.fit(X_train,y_train,validation_split=1.07,epochs=6,batch_size=32)

#dataset_total = pd.concat((dataset["High"][:'2016'],dataset["High"]['2017':]),axis=0)
inputs = df['Energy'][len(df['Energy'])-len(test_set) - 48:].values
inputs = inputs.reshape(-1,1)
inputs  = sc.transform(inputs)

X_test = []
for i in range(48,len(test_set)):
    X_test.append(inputs[i-48:i,0])
X_test = np.array(X_test)
X_test = np.reshape(X_test, (X_test.shape[0],X_test.shape[1],1))
predicted_power = model.predict(X_test)
predicted_power = sc.inverse_transform(predicted_power)

print("LSTM's RMSE:",np.sqrt(mean_squared_error(predicted_power-213,test_set[:48])))
#plot_predictions(test_set,predicted_power-230)
'''
print(" Fitting N-beats ... ")
from nbeats_forecast import NBeats
from torch import optim

nbeats_bound = df.shape[0]-48
n_b  = df['Energy'][:nbeats_bound] 
test = df['Energy'][-48:].values
data = n_b.values    
data = np.reshape(data,(len(data),1))    #univariate time series data of shape nx1 (numpy array)

model=NBeats(data=data,period_to_forecast=48,stack=[2,3],nb_blocks_per_stack=3,thetas_dims=[2,8])

model.fit(epoch=5,optimiser=optim.AdamW(model.parameters, lr=0.001, betas=(0.9, 0.999), eps=1e-08, weight_decay=0.01, amsgrad=False))

forecast=model.predict()

print("N-beats Score:",np.sqrt(mean_squared_error(forecast-55,test)))

print(" Fitting Polynomial Regression (polynomial features are king)...")
X = df[['Wind_Speed','Wind_Direction','Precipitation','Humidity','Pressure','Temperature','Avg_temp','Code','Dew_Point','Energy']].copy()

linear_bound = X.shape[0]-48

X_train =  X[:linear_bound]
X_test  =  X[-48:]
y_train =  X_train['Energy']
y_test  =  X_test['Energy']
X_train.drop(['Energy'],axis=1,inplace=True)
X_test.drop(['Energy'],axis=1,inplace=True)

poly = PolynomialFeatures(degree=5)
poly_X_train_confirmed = poly.fit_transform(X_train)
poly_X_test_confirmed = poly.fit_transform(X_test)

linear_model = LinearRegression(normalize=True, fit_intercept=False)
linear_model.fit(poly_X_train_confirmed, y_train)
test_linear_pred = linear_model.predict(poly_X_test_confirmed)

print('Polynomial feature regressions RMSE:',np.sqrt(mean_squared_error(test_linear_pred, y_test)))

XGB_result.index = XGB_result.index.astype('string')
XGB_result.drop(['Theoretical'],axis=1,inplace=True)
XGB_result.to_csv("Dhalgaon_Predictions_Ady.csv")
XGB_result=XGB_result.T
XGB_result.to_json('Dhalgaon_Predictions.json', orient='records')

end_time = datetime.now()
print("Time required to run a single script:", end_time - start_time)