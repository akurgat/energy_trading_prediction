from trading_ig import IGService
from trading_ig.config import config
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# if you need to cache to DB your requests
from datetime import timedelta
import requests_cache
import matplotlib.pyplot as plt
from model import data_preprocessing, buy_sell_prediction, buy_sell_prediction_model, price_prediction, price_prediction_model

def back_testing(df):
    
    #Preprocess the data
    df = data_preprocessing(df, df['Close'], df['High'], df['Low'],)
    #Predict the possible buy sell signal
    predicted_buy_or_sell = buy_sell_prediction(df, buy_sell_prediction_model)
    #Predict the possible close price
    predicted_price = price_prediction(df, price_prediction_model) 
    
    #Normalize the length of the dataframe and the predictions
    df_length = predicted_price.shape[0]
    df = df.iloc[-df_length:]
    df['Predicted_Price'] = predicted_price
    df_length = predicted_buy_or_sell.shape[0]
    df = df.iloc[-df_length:]
    df['Buy_or_Sell_Action'] = predicted_buy_or_sell

    #Update the buy sell hold indications from the predictions for graphing purposes
    df.loc[((df['Buy_or_Sell_Action'] == 'Buy')), 'Predicted_Action_Buy'] = 1
    df.loc[((df['Buy_or_Sell_Action'] == 'Sell')), 'Predicted_Action_Sell'] = 1
    df.loc[((df['Buy_or_Sell_Action'] == 'Hold')), 'Predicted_Action_Hold'] = 1
    df['Predicted_Action_Buy'].fillna(0, inplace = True)
    df['Predicted_Action_Sell'].fillna(0, inplace = True)
    df['Predicted_Action_Hold'].fillna(0, inplace = True)
    
    #Redefine the dataframe bases on the needed columns
    #STOCH, RSI, MACD not currently being used for visualization but can be if need be in the future
    df = df[['Close', 'Predicted_Price', 'Predicted_Action_Buy', 'Predicted_Action_Sell', 
             'Predicted_Action_Hold', '%K', '%D', 'RSI', 'MACD', 'MACDS', 'MACDH']]
    
    return df
    

def main():
    logging.basicConfig(level=logging.DEBUG)

    expire_after = timedelta(hours=1)
    session = requests_cache.CachedSession(
        cache_name='cache', backend='sqlite', expire_after=expire_after)
    # set expire_after=None if you don't want cache expiration
    # set expire_after=0 if you don't want to cache queries

    #config = IGServiceConfig()

    # no cache
    ig_service = IGService(config.username, config.password, config.api_key, config.acc_type)

    # if you want to globally cache queries
    #ig_service = IGService(config.username, config.password, config.api_key, config.acc_type, session)

    ig_service.create_session()

    #epic = 'CS.D.EURUSD.MINI.IP'
    epic = 'CC.D.NG.USS.IP'  # US (SPY) - mini

    #resolution = 'D'
    # see from pandas.tseries.frequencies import to_offset
    #resolution = 'H'
    resolution = '5Min'
    (start_date, end_date) = ('2020-01-23', '2020-01-25')

    num_points = 200 #Number of data points should be at least 50 to accommodate technical indications calculations
    response = ig_service.fetch_historical_prices_by_epic_and_num_points(epic, resolution, num_points)
    
    #response = ig_service.fetch_historical_prices_by_epic_and_date_range(epic, resolution, start_date, end_date)

    # if you want to cache this query
    #response = ig_service.fetch_historical_prices_by_epic_and_date_range(epic, resolution, start_date, end_date, session)
   
    #response = ig_service.fetch_historical_prices_by_epic_and_num_points(epic, resolution, num_points, session)
    
    df_ask = response['prices']['ask']
    
    df_ask = back_testing(df_ask) #Analyse the received data set
    
    #Graphing the historical close price trends, predicted prices and buy sell points
    fig, ax = plt.subplots()

    plt.gcf().set_size_inches(22, 15, forward=True)
    plt.gcf().set_facecolor('xkcd:white')

    #Visualize the buy-sell indication to identify buy sell regions in a graph based on the predictions
    ax = df_ask['Predicted_Action_Buy'].plot(alpha = 0.3, kind = 'bar', color = 'green', label = 'Buy')
    ax = df_ask['Predicted_Action_Sell'].plot(alpha = 0.3, kind = 'bar', color = 'red', label = 'Sell')
    ax = df_ask['Predicted_Action_Hold'].plot(alpha = 0.3, kind = 'bar', color = 'white', label = 'Hold')

    ax.legend(loc = 2)#Position the Buy-Sell-Hold ledgend to the upper left corner	

    ax2 = ax.twinx()#Create another chart on the same figure
    #Visualize the close and predicted price line charts on the same axis
    ax2.plot(ax.get_xticks(), df_ask['Close'], alpha = 0.85, color = 'orange', label = 'Actual Price')
    ax2.plot(ax.get_xticks(), df_ask['Predicted_Price'], alpha = 0.85, color = 'blue', label = 'Predicted Price')
	
    ax2.legend(loc = 1)#Position the Buy-Sell-Hold ledgend to the upper right corner
    plt.title('Historical Price Movement')# Setting chart title
	#Setting axis names
    plt.xlabel('DateTime')
    plt.ylabel('Price')

    plt.show()#Display the graph

if __name__ == '__main__':
    main()