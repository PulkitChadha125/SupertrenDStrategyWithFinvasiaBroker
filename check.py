enable_trading = "True"
import json
import math
from sched import scheduler
import schedule
import finvasia
from kite_trade import *
from datetime import datetime, timedelta
import threading
import time as sleep_time
import pandas as pd
import pandas_ta as ta
from apscheduler.schedulers.background import BackgroundScheduler
import time
from finvasia import *

runner = True
a = False
b = False
finvasia.autologin()
signals_list = []
# logs not getting generated
signal_dict = {}
end_time_str = None
start_time_str = None
lock = threading.Lock()


def read_csv_to_dictionary(file_path):
    data_dict = {}
    global signal_dict, end_time_str, start_time_str

    df = pd.read_csv(file_path)
    for index, row in df.iterrows():
        strategy_tag = row['strategyTag']
        data_dict[strategy_tag] = row.to_dict()

        signal_dict[strategy_tag] = {'Buy': False, 'Sell': False, 'IntialTrade': False, 'Target': None,
                                     'Stoploss': None, 'PreviousString': None, "T": False, "S": False, "Count": 0,
                                     "expiry": None, "max_trades": None, "ProductType": None, "Quantity": None}

    start_time_str = data_dict['STG1']['StartTime']
    start_time_str = datetime.strptime(start_time_str, '%H:%M').time()
    end_time_str = data_dict['STG1']['EndTime']
    end_time_str = datetime.strptime(end_time_str, '%H:%M').time()
    print(start_time_str)
    print(end_time_str)

    return data_dict


data_dict = read_csv_to_dictionary(
    "C:\\Users\\Administrator\\Desktop\\Anil kholi supertrend\\Anil kholi supertrend\\TradeSettings.csv")


def process_data(data_dict):
    strikefinal = None
    supertrend_multiplier = None
    supertrend_period = None
    symbol = None
    strategy_signal = None
    option_contract_type = None
    strike_distance = None
    expiry = None
    lot_size = None
    Product = None
    stop_loss = None
    take_profit = None

    global signals_list, signal_dict

    for strategy_tag, data in data_dict.items():
        if pd.notna(strategy_tag):
            symbol = data['symbol']
            timeframe = data['Timeframe']
            supertrend_period = data['Supertrend period']
            supertrend_multiplier = data['Supertrend Multiplier']
            option_contract_type = data['OPTION CONTRACT TYPE']
            strike_distance = data['strike distance']
            expiry = data['expiery']
            expiry = datetime.strptime(expiry, "%d-%b-%y")
            expiry = expiry.strftime("%d%b%y").upper()
            signal_dict[strategy_tag]['expiry'] = expiry

            print(signal_dict[strategy_tag]['expiry'])
            max_trades = data['MAX trades']
            signal_dict[strategy_tag]['max_trades'] = max_trades
            stop_loss = data['Stoloss']
            take_profit = data['TakeProfit']
            lot_size = data['lotsize']
            Nifty_instrument_token = None
            BankNifty_instrument_token = None
            Product = data['Product']

            finvasia.get_historical_data(symbol=symbol, timeframe=timeframe, strategy_tag=strategy_tag,
                                         supertrend_period=supertrend_period,
                                         supertrend_multiplier=supertrend_multiplier)

            print("Error happning in main.....................")
            df = pd.read_csv(
                f'C:\\Users\\Administrator\\Desktop\\Anil kholi supertrend\\Anil kholi supertrend\\{strategy_tag}.csv')
            print("Error happning in main......")
            last_supertrend_signal = df['Supertrend Signal'].iloc[-1]
            second_last_supertrend_signal = df['Supertrend Signal'].iloc[-2]
            third_last_supertrend_signal = df['Supertrend Signal'].iloc[-3]

            usedltp = None
            option_contract_type = data['OPTION CONTRACT TYPE']
            strike_distance = data['strike distance']

            if symbol == "NIFTY":
                usedltp = finvasia.get_ltp(symbol)

            if symbol == "BANKNIFTY":
                usedltp = finvasia.get_ltp(symbol)

            timestamp = datetime.now()
            timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")

            # print("usedltp= ",usedltp)
            print("strategy_tag=", strategy_tag)
            print("supertrend_period=", supertrend_period)
            print("supertrend_multiplier=", supertrend_multiplier)
            print("last_supertrend_signal=", last_supertrend_signal)
            print("second_last_supertrend_signal =", second_last_supertrend_signal)
            print("third_last_supertrend_signal =", third_last_supertrend_signal)

            if last_supertrend_signal == -1 and signal_dict[strategy_tag]['Sell'] == False and \
                    signal_dict[strategy_tag]['IntialTrade'] == False and int(
                signal_dict[strategy_tag]['Count']) <= int(signal_dict[strategy_tag]['max_trades']):

                strategy_signal = 'Sell'
                signal_dict[strategy_tag]['IntialTrade'] = True
                signal_dict[strategy_tag]['Buy'] = False
                signal_dict[strategy_tag]['Sell'] = True
                signal_dict[strategy_tag]['Count'] = int(signal_dict[strategy_tag]['Count']) + 1

                if option_contract_type == "ATM":
                    strikefinal = custom_round(price=int(float(usedltp)), symbol=data_dict[strategy_tag]['symbol'])
                    pe_strike = strikefinal
                if option_contract_type == "ITM":
                    strikefinal = custom_round(price=int(float(usedltp)), symbol=data_dict[strategy_tag]['symbol'])
                    pe_strike = int(strikefinal) + strike_distance

                if option_contract_type == "OTM":
                    strikefinal = custom_round(price=int(float(usedltp)), symbol=data_dict[strategy_tag]['symbol'])
                    pe_strike = int(strikefinal) - strike_distance
                # symstring needs to be calculated

                symstring = f"{symbol} {signal_dict[strategy_tag]['expiry']} {int(pe_strike)} PE"
                print(symstring)

                if enable_trading == "True":
                    finvasia.buy_order(tradingsymbol=symstring, quantity=int(lot_size), Product_Type=Product)

                script_ltp = finvasia.get_option_detail(tradingsymbol=symstring)
                print(script_ltp)
                signal_dict[strategy_tag]['Target'] = float(script_ltp) + float(take_profit)
                signal_dict[strategy_tag]['Stoploss'] = float(script_ltp) - float(stop_loss)
                signal_dict[strategy_tag]['T'] = True
                signal_dict[strategy_tag]['S'] = True
                signal_dict[strategy_tag]['ProductType'] = Product
                signal_dict[strategy_tag]['Quantity'] = int(lot_size)

                orderlog = f"{timestamp} Initial Order for Sell From {strategy_tag} @ BaseSymbol: {data_dict[strategy_tag]['symbol']} @ price: {usedltp} , Buy PE = {pe_strike}  , expiery={expiry},OptionEntryPrice={script_ltp}, Optin Target Value= {signal_dict[strategy_tag]['Target']} ,Option Stoploss Value {signal_dict[strategy_tag]['Stoploss']}"
                print("orderlog= ", orderlog)
                write_to_order_logs(orderlog)

                signal_dict[strategy_tag]['PreviousString'] = symstring
                print("PreviousString: ", signal_dict[strategy_tag]['PreviousString'])

            if last_supertrend_signal == 1 and signal_dict[strategy_tag]['Buy'] == False and signal_dict[strategy_tag][
                'IntialTrade'] == False and int(signal_dict[strategy_tag]['Count']) <= int(
                signal_dict[strategy_tag]['max_trades']):
                signal_dict[strategy_tag]['IntialTrade'] = True
                strategy_signal = 'Buy'
                signal_dict[strategy_tag]['Buy'] = True
                signal_dict[strategy_tag]['Sell'] = False
                signal_dict[strategy_tag]['Count'] = int(signal_dict[strategy_tag]['Count']) + 1
                # jb bhi sell hoga pe buy hoga
                # jb bhi buy hoga ce buy hoga

                if option_contract_type == "ATM":
                    strikefinal = custom_round(price=int(float(usedltp)), symbol=data_dict[strategy_tag]['symbol'])
                    ce_strike = strikefinal
                if option_contract_type == "ITM":
                    strikefinal = custom_round(price=int(float(usedltp)), symbol=data_dict[strategy_tag]['symbol'])
                    ce_strike = int(strikefinal) - strike_distance

                if option_contract_type == "OTM":
                    strikefinal = custom_round(price=int(float(usedltp)), symbol=data_dict[strategy_tag]['symbol'])
                    ce_strike = int(strikefinal) + strike_distance
                # NIFTY07SEP23C16650
                symstring = f"{symbol} {signal_dict[strategy_tag]['expiry']} {int(ce_strike)} CE"
                print(symstring)
                # symstring needs to be calculated
                signal_dict[strategy_tag]['Target'] = float(script_ltp) + float(take_profit)
                signal_dict[strategy_tag]['Stoploss'] = float(script_ltp) - float(stop_loss)
                signal_dict[strategy_tag]['T'] = True
                signal_dict[strategy_tag]['S'] = True
                signal_dict[strategy_tag]['ProductType'] = Product
                signal_dict[strategy_tag]['Quantity'] = int(lot_size)

                orderlog = f"{timestamp} Initial Order for Buy From {strategy_tag} @ BaseSymbol: {data_dict[strategy_tag]['symbol']} @ price: {usedltp} , Buy CE = {ce_strike}  , expiery={expiry},OptionEntryPrice={script_ltp}, Optin Target Value= {signal_dict[strategy_tag]['Target']} ,Option Stoploss Value {signal_dict[strategy_tag]['Stoploss']}"
                print("orderlog= ", orderlog)
                write_to_order_logs(orderlog)
                if enable_trading == "True":
                    finvasia.buy_order(tradingsymbol=symstring, quantity=int(lot_size), Product_Type=Product)

                script_ltp = finvasia.get_option_detail(tradingsymbol=symstring)
                print(script_ltp)
                signal_dict[strategy_tag]['Target'] = float(script_ltp) + float(take_profit)
                signal_dict[strategy_tag]['Stoploss'] = float(script_ltp) - float(stop_loss)
                signal_dict[strategy_tag]['T'] = True
                signal_dict[strategy_tag]['S'] = True
                signal_dict[strategy_tag]['ProductType'] = Product
                signal_dict[strategy_tag]['Quantity'] = int(lot_size)

                signal_dict[strategy_tag]['PreviousString'] = symstring
                print("PreviousString: ", signal_dict[strategy_tag]['PreviousString'])
                write_to_order_logs(signal_dict)

            if last_supertrend_signal == 1 and second_last_supertrend_signal == -1 and signal_dict[strategy_tag][
                'Buy'] == False and signal_dict[strategy_tag]['IntialTrade'] == True and int(
                signal_dict[strategy_tag]['Count']) <= int(signal_dict[strategy_tag]['max_trades']):
                strategy_signal = 'Buy'
                signal_dict[strategy_tag]['Buy'] = True
                signal_dict[strategy_tag]['Sell'] = False
                signal_dict[strategy_tag]['Count'] = int(signal_dict[strategy_tag]['Count']) + 1

                if option_contract_type == "ATM":
                    strikefinal = custom_round(price=int(float(usedltp)), symbol=data_dict[strategy_tag]['symbol'])
                    ce_strike = strikefinal
                if option_contract_type == "ITM":
                    strikefinal = custom_round(price=int(float(usedltp)), symbol=data_dict[strategy_tag]['symbol'])
                    ce_strike = int(strikefinal) - strike_distance

                if option_contract_type == "OTM":
                    strikefinal = custom_round(price=int(float(usedltp)), symbol=data_dict[strategy_tag]['symbol'])
                    ce_strike = int(strikefinal) + strike_distance

                symstring = f"{symbol} {signal_dict[strategy_tag]['expiry']} {int(ce_strike)} CE"
                print("symstring= ", symstring)
                print("PreviousString= ", signal_dict[strategy_tag]['PreviousString'])
                if enable_trading == "True":
                    if signal_dict[strategy_tag]['T'] == True and int(finvasia.get_position_detail(
                            symbol_to_find=signal_dict[strategy_tag]['PreviousString'])) > 0:
                        finvasia.sell_order(tradingsymbol=signal_dict[strategy_tag]['PreviousString'],
                                            quantity=int(lot_size), Product_Type=Product)
                    finvasia.buy_order(tradingsymbol=symstring, quantity=int(lot_size), Product_Type=Product)

                script_ltp = finvasia.get_option_detail(tradingsymbol=symstring)
                print(script_ltp)

                signal_dict[strategy_tag]['Target'] = float(script_ltp) + float(take_profit)
                signal_dict[strategy_tag]['Stoploss'] = float(script_ltp) - float(stop_loss)
                signal_dict[strategy_tag]['T'] = True
                signal_dict[strategy_tag]['S'] = True
                signal_dict[strategy_tag]['ProductType'] = Product
                signal_dict[strategy_tag]['Quantity'] = int(lot_size)

                orderlog = f"{timestamp}  Order for Buy From {strategy_tag} @ BaseSymbol: {data_dict[strategy_tag]['symbol']} @ price: {usedltp} , Buy CE = {ce_strike}  , expiery={expiry},OptionEntryPrice={script_ltp}, Optin Target Value= {signal_dict[strategy_tag]['Target']} ,Option Stoploss Value {signal_dict[strategy_tag]['Stoploss']}"
                print("orderlog= ", orderlog)
                write_to_order_logs(orderlog)

                signal_dict[strategy_tag]['PreviousString'] = symstring
                write_to_order_logs(signal_dict)

            if last_supertrend_signal == -1 and second_last_supertrend_signal == 1 and signal_dict[strategy_tag][
                'Sell'] == False and signal_dict[strategy_tag]['IntialTrade'] == True and int(
                signal_dict[strategy_tag]['Count']) <= int(signal_dict[strategy_tag]['max_trades']):
                strategy_signal = 'Sell'
                signal_dict[strategy_tag]['Buy'] = False
                signal_dict[strategy_tag]['Sell'] = True
                signal_dict[strategy_tag]['Count'] = int(signal_dict[strategy_tag]['Count']) + 1

                if option_contract_type == "ATM":
                    strikefinal = custom_round(price=int(float(usedltp)), symbol=data_dict[strategy_tag]['symbol'])
                    pe_strike = strikefinal
                if option_contract_type == "ITM":
                    strikefinal = custom_round(price=int(float(usedltp)), symbol=data_dict[strategy_tag]['symbol'])
                    pe_strike = int(strikefinal) + strike_distance

                if option_contract_type == "OTM":
                    strikefinal = custom_round(price=int(float(usedltp)), symbol=data_dict[strategy_tag]['symbol'])
                    pe_strike = int(strikefinal) - strike_distance

                symstring = f"{symbol} {signal_dict[strategy_tag]['expiry']} {int(pe_strike)} PE"
                print("symstring= ", symstring)
                print("PreviousString= ", signal_dict[strategy_tag]['PreviousString'])
                if enable_trading == "True":
                    if signal_dict[strategy_tag]['T'] == True and int(finvasia.get_position_detail(
                            symbol_to_find=signal_dict[strategy_tag]['PreviousString'])) > 0:
                        finvasia.sell_order(tradingsymbol=signal_dict[strategy_tag]['PreviousString'],
                                            quantity=int(lot_size), Product_Type=Product)
                    symstring = f"{symbol} {signal_dict[strategy_tag]['expiry']} {int(pe_strike)} PE"
                    finvasia.buy_order(tradingsymbol=symstring, quantity=int(lot_size), Product_Type=Product)

                script_ltp = finvasia.get_option_detail(tradingsymbol=symstring)
                print(script_ltp)

                signal_dict[strategy_tag]['Target'] = float(script_ltp) + float(take_profit)
                signal_dict[strategy_tag]['Stoploss'] = float(script_ltp) - float(stop_loss)
                signal_dict[strategy_tag]['T'] = True
                signal_dict[strategy_tag]['S'] = True
                signal_dict[strategy_tag]['ProductType'] = Product
                signal_dict[strategy_tag]['Quantity'] = int(lot_size)

                orderlog = f"{timestamp} Order for Sell From {strategy_tag} @ BaseSymbol: {data_dict[strategy_tag]['symbol']} @ price: {usedltp} , Buy PE = {pe_strike}  , expiery={expiry},OptionEntryPrice={script_ltp}, Optin Target Value= {signal_dict[strategy_tag]['Target']} ,Option Stoploss Value {signal_dict[strategy_tag]['Stoploss']}"
                print("orderlog= ", orderlog)
                write_to_order_logs(orderlog)

                signal_dict[strategy_tag]['PreviousString'] = symstring
                write_to_order_logs(signal_dict)

            df['strategy_signal'] = strategy_signal
            df.to_csv(
                f'C:\\Users\\Administrator\\Desktop\\Anil kholi supertrend\\Anil kholi supertrend\\{strategy_tag}.csv')


def write_to_order_logs(message):
    with open('C:\\Users\\Administrator\\Desktop\\Anil kholi supertrend\\Anil kholi supertrend\\order_logs.txt',
              'a') as file:
        file.write(message + '\n')


def clear_file(file_path):
    with open(file_path, 'w') as file:
        file.truncate(0)


def custom_round(price, symbol):
    rounded_price = None

    if symbol == "NIFTY":
        last_two_digits = price % 100
        if last_two_digits < 25:
            rounded_price = (price // 100) * 100
        elif last_two_digits < 75:
            rounded_price = (price // 100) * 100 + 50
        else:
            rounded_price = (price // 100 + 1) * 100
            return rounded_price

    elif symbol == "BANKNIFTY":
        last_two_digits = price % 100
        if last_two_digits < 50:
            rounded_price = (price // 100) * 100
        else:
            rounded_price = (price // 100 + 1) * 100
        return rounded_price

    else:
        pass

    return rounded_price


def run_process_data():
    global end_time_str, start_time_str
    timestamp = datetime.now()
    timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")
    current_time = datetime.now().time()
    if start_time_str and end_time_str and start_time_str <= current_time <= end_time_str:
        print(f"{timestamp} Running process_data...")
        with lock:
            process_data(data_dict)


def tp_and_sl(signal_dict):
    timestamp = datetime.now()
    timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")
    for strategy_tag, data in data_dict.items():
        if pd.notna(strategy_tag):

            if signal_dict[strategy_tag]['T'] == True and signal_dict[strategy_tag]['Buy'] == True and int(
                    finvasia.get_position_detail(symbol_to_find=signal_dict[strategy_tag]['PreviousString'])) > 0:
                option_script_ltp = finvasia.get_option_detail(
                    tradingsymbol=signal_dict[strategy_tag]['PreviousString'])
                if float(option_script_ltp) >= float(signal_dict[strategy_tag]['Target']):
                    signal_dict[strategy_tag]['T'] = False
                    signal_dict[strategy_tag]['S'] = False
                    orderlog = f"{timestamp} Target executed for Buy trade {strategy_tag}  For option contract  = {signal_dict[strategy_tag]['PreviousString']} @ {option_script_ltp}"
                    finvasia.sell_order(tradingsymbol=signal_dict[strategy_tag]['PreviousString'],
                                        quantity=int(signal_dict[strategy_tag]['Quantity']),
                                        Product_Type=signal_dict[strategy_tag]['ProductType'])
                    print("orderlog= ", orderlog)
                    write_to_order_logs(orderlog)
                    print("signal_dict= ", signal_dict)

                if signal_dict[strategy_tag]['T'] == True and signal_dict[strategy_tag]['Sell'] == True:
                    option_script_ltp = finvasia.get_option_detail(
                        tradingsymbol=signal_dict[strategy_tag]['PreviousString'])
                    if float(option_script_ltp) >= float(signal_dict[strategy_tag]['Target']):
                        signal_dict[strategy_tag]['T'] = False
                        signal_dict[strategy_tag]['S'] = False
                        orderlog = f"{timestamp} Target executed for Sell trade {strategy_tag}  For option contract  = {signal_dict[strategy_tag]['PreviousString']} @ {option_script_ltp}"
                        finvasia.sell_order(tradingsymbol=signal_dict[strategy_tag]['PreviousString'],
                                            quantity=int(signal_dict[strategy_tag]['Quantity']),
                                            Product_Type=signal_dict[strategy_tag]['ProductType'])
                        print("orderlog= ", orderlog)
                        write_to_order_logs(orderlog)
                        print("signal_dict= ", signal_dict)

                if signal_dict[strategy_tag]['S'] == True and signal_dict[strategy_tag]['Buy'] == True:
                    option_script_ltp = finvasia.get_option_detail(
                        tradingsymbol=signal_dict[strategy_tag]['PreviousString'])
                    if float(option_script_ltp) <= float(signal_dict[strategy_tag]['Stoploss']):
                        signal_dict[strategy_tag]['T'] = False
                        signal_dict[strategy_tag]['S'] = False
                        orderlog = f"{timestamp} Stoploss executed for Buy trade {strategy_tag}  For option contract  = {signal_dict[strategy_tag]['PreviousString']} @ {option_script_ltp}"
                        finvasia.sell_order(tradingsymbol=signal_dict[strategy_tag]['PreviousString'],
                                            quantity=int(signal_dict[strategy_tag]['Quantity']),
                                            Product_Type=signal_dict[strategy_tag]['ProductType'])
                        print("orderlog= ", orderlog)
                        write_to_order_logs(orderlog)
                        print("signal_dict= ", signal_dict)

                if signal_dict[strategy_tag]['S'] == True and signal_dict[strategy_tag]['Sell'] == True:
                    option_script_ltp = finvasia.get_option_detail(
                        tradingsymbol=signal_dict[strategy_tag]['PreviousString'])
                    if float(option_script_ltp) <= float(signal_dict[strategy_tag]['Stoploss']):
                        signal_dict[strategy_tag]['T'] = False
                        signal_dict[strategy_tag]['S'] = False
                        orderlog = f"{timestamp} Stoploss executed for Sell trade {strategy_tag}  For option contract  = {signal_dict[strategy_tag]['PreviousString']} @ {option_script_ltp}"
                        finvasia.sell_order(tradingsymbol=signal_dict[strategy_tag]['PreviousString'],
                                            quantity=int(signal_dict[strategy_tag]['Quantity']),
                                            Product_Type=signal_dict[strategy_tag]['ProductType'])
                        print("orderlog= ", orderlog)
                        write_to_order_logs(orderlog)
                        print("signal_dict= ", signal_dict)


def schedule_process_data():
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_process_data, 'interval', minutes=1)
    scheduler.start()


if __name__ == "__main__":
    now = datetime.now()
    seconds_until_next_minute = 60 - now.second

    initial_delay = seconds_until_next_minute + 1

    schedule_process_data()

    try:
        while True:
            timestamp = datetime.now()
            timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")
            current_time = datetime.now().time()
            # Only allow one of the functions to run at a time

            with lock:
                tp_and_sl(signal_dict)
            sleep_time.sleep(1)  # Keep the main thread alive
    except (KeyboardInterrupt, SystemExit):

        pass  # Gracefully exit the loop when interrupted hh