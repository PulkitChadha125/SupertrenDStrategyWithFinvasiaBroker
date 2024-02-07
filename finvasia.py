from NorenRestApiPy.NorenApi import  NorenApi
import pandas as pd
import logging
import pyotp
from datetime import datetime, timedelta
import pandas_ta as ta


# Get the current date and time
current_date_time = datetime.today()

current_date_time = current_date_time - timedelta(days=2)
current_date_time = current_date_time .replace(hour=0,minute=0,second=0,microsecond=0)

# Convert both dates to Unix timestamp format
current_date_time = current_date_time.timestamp()
api=None
def delete_file_contents(file_name):
    try:
        # Open the file in write mode, which truncates it (deletes contents)
        with open(file_name, 'w') as file:
            file.truncate(0)
        print(f"Contents of {file_name} have been deleted.")
    except FileNotFoundError:
        print(f"File {file_name} not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

class ShoonyaApiPy(NorenApi):
    def __init__(self):
        NorenApi.__init__(self, host='https://api.shoonya.com/NorenWClientTP/', websocket='wss://api.shoonya.com/NorenWSTP/')
        global api
        api = self
# enable dbug to see request and responses
logging.basicConfig(level=logging.DEBUG)




def autologin():
    global api
    delete_file_contents("order_logs.txt")
    api = ShoonyaApiPy()
    token = "G3V7FI3TX7DH2AC2IO52AQ53V3PPB253"
    totp=pyotp.TOTP(token).now()
    print(totp)

    # credentials
    user ='FA150539'
    pwd = 'A10w@rthog'
    factor2 =totp
    vc = 'FA150539_U'
    app_key = '83196c05552ea704c32fae23217d68b7'
    imei = 'abc1234'


    ret = api.login(userid=user, password=pwd, twoFA=factor2, vendor_code=vc, api_secret=app_key, imei=imei)
    print("Autologin to fnvasia compleated ...")




def get_historical_data(symbol,timeframe,strategy_tag,supertrend_period,supertrend_multiplier):
    global api

    ret2 = api.searchscrip('NSE', 'NIFTY')
    df = pd.DataFrame(ret2['values'])
    print(df)

    if symbol=="NIFTY":
        target_strings = ["NIFTY INDEX"]
    if symbol=="BANKNIFTY":
        target_strings = ["NIFTY BANK"]

    # Initialize a dictionary to store the results
    token_values = {}

    # Loop through the target strings and find the 'token' value for each
    for target_string in target_strings:
        filtered_df = df[df['cname'].str.contains(target_string, case=False)]
        if not filtered_df.empty:
            token_value = filtered_df.iloc[0]['token']
            token_values[target_string] = token_value


    historical=api.get_time_price_series(exchange="NSE",token=str(token_value),starttime=current_date_time,interval=timeframe)
    df=pd.DataFrame(historical)
    df.to_csv("Inslist.csv")

    df = pd.read_csv("Inslist.csv")

    # Adjust the format string to include seconds if needed
    df['time'] = pd.to_datetime(df['time'], format='%d-%m-%Y %H:%M:%S')

    # Sort the DataFrame by the "time" column in descending order
    df = df.sort_values(by="time", ascending=True)  # Change ascending to True to sort in ascending order
    colname = f'SUPERT_{int(supertrend_period)}_{supertrend_multiplier}'
    colname2 = f'SUPERTd_{int(supertrend_period)}_{supertrend_multiplier}'

    df["Supertrend Values"] = ta.supertrend(high=df['inth'], low=df['intl'], close=df['intc'], length=supertrend_period, multiplier=supertrend_multiplier)[colname]
    df["Supertrend Signal"] = ta.supertrend(high=df['inth'], low=df['intl'], close=df['intc'], length=supertrend_period, multiplier=supertrend_multiplier)[colname2]

    # Save the updated DataFrame back to the CSV file
    df.to_csv(f'{strategy_tag}.csv', index=False)


def get_ltp (symbol):
    global api
    ret2 = api.searchscrip('NSE', 'NIFTY')
    df = pd.DataFrame(ret2['values'])

    if symbol == "NIFTY":
        target_strings = ["NIFTY INDEX"]
    if symbol == "BANKNIFTY":
        target_strings = ["NIFTY BANK"]

    # Initialize a dictionary to store the results
    token_values = {}

    # Loop through the target strings and find the 'token' value for each
    for target_string in target_strings:
        filtered_df = df[df['cname'].str.contains(target_string, case=False)]
        if not filtered_df.empty:
            token_value = filtered_df.iloc[0]['token']
            token_values[target_string] = token_value

    requiredltp = api.get_quotes(exchange="NSE", token=str(token_value))

    requiredltp=requiredltp['lp']


    return requiredltp

def buy_order(tradingsymbol,quantity,Product_Type):
    global api
    # NIFTY07SEP23C16650
    scriptdetail = api.searchscrip('NFO', tradingsymbol)
    scriptdetail = scriptdetail["values"][0]["tsym"]
    print("scriptdetail=", api.searchscrip('NFO', tradingsymbol))

    pt=None
    if Product_Type=="MIS":
        pt="I"
    if Product_Type=="NRML":
        pt="M"
    if Product_Type=="CNC":
        pt="C"


    order_detail = api.place_order(buy_or_sell='B',
                                   product_type=pt,
                                    exchange='NFO',
                                   tradingsymbol=scriptdetail,
                                   quantity=quantity,
                                   discloseqty=0,
                                   price_type='MKT',
                                   price=0,
                                   trigger_price=0,
                                   retention='DAY',
                                   remarks='my_order')

    BuyEntryOrderNumber = order_detail['norenordno']
    print("Buy Entry Order Number= ", BuyEntryOrderNumber)

def sell_order(tradingsymbol,quantity,Product_Type):
    global api
    # NIFTY07SEP23C16650
    scriptdetail = api.searchscrip('NFO', tradingsymbol)
    scriptdetail = scriptdetail["values"][0]["tsym"]
    # print("scriptdetail=", scriptdetail)
    pt = None
    if Product_Type == "MIS":
        pt = "I"
    if Product_Type == "NRML":
        pt = "M"
    if Product_Type == "CNC":
        pt = "C"

    order_detail = api.place_order(buy_or_sell='S',
                                   product_type=pt,
                                   exchange='NFO',
                                   tradingsymbol=scriptdetail,
                                   quantity=quantity,
                                   discloseqty=0,
                                   price_type='MKT',
                                   price=0,
                                   trigger_price=0,
                                   retention='DAY',
                                   remarks='my_order')

    BuyExitOrderNumber=order_detail['norenordno']
    print("Buy Exit OrderNumber= ", BuyExitOrderNumber)

def short_order(tradingsymbol,quantity,Product_Type):
    global api
    # NIFTY07SEP23C16650
    scriptdetail= api.searchscrip('NFO', tradingsymbol)
    scriptdetail=scriptdetail["values"][0]["tsym"]
    # print("scriptdetail=",scriptdetail)





    pt=None
    if Product_Type=="MIS":
        pt="I"
    if Product_Type=="NRML":
        pt="M"
    if Product_Type=="CNC":
        pt="C"


    order_detail = api.place_order(buy_or_sell='S',
                                   product_type=pt,
                                    exchange='NFO',
                                   tradingsymbol=scriptdetail,
                                   quantity=quantity,
                                   discloseqty=0,
                                   price_type='MKT',
                                   price=0,
                                   trigger_price=0,
                                   retention='DAY',
                                   remarks='my_order')

    SellEntryOrderNumber = order_detail['norenordno']
    print("Sell Entry OrderNumber= ", SellEntryOrderNumber)

def cover_order(tradingsymbol,quantity,Product_Type):
    global api

    # NIFTY07SEP23C16650
    scriptdetail = api.searchscrip('NFO', tradingsymbol)
    scriptdetail = scriptdetail["values"][0]["tsym"]
    # print("scriptdetail=", scriptdetail)
    pt = None
    if Product_Type == "MIS":
        pt = "I"
    if Product_Type == "NRML":
        pt = "M"
    if Product_Type == "CNC":
        pt = "C"

    order_detail = api.place_order(buy_or_sell='B',
                                   product_type=pt,
                                   exchange='NFO',
                                   tradingsymbol=scriptdetail,
                                   quantity=quantity,
                                   discloseqty=0,
                                   price_type='MKT',
                                   price=0,
                                   trigger_price=0,
                                   retention='DAY',
                                   remarks='my_order')

    SellExitOrderNumber = order_detail['norenordno']
    print("Buy Exit OrderNumber= ", SellExitOrderNumber)


def get_option_detail(tradingsymbol):
    global api
    # NIFTY07SEP23C16650
    scriptdetail = api.searchscrip('NFO', tradingsymbol)
    scriptdetail = scriptdetail["values"][0]["token"]
    scriptdetail_ltp=api.get_quotes(exchange="NFO", token=scriptdetail)
    scriptdetail_ltp=scriptdetail_ltp['lp']

    return scriptdetail_ltp


def get_position_detail(symbol_to_find):
    global api
    ret = api.get_positions()
    net_qty = 0  # Initialize net_qty to None

    if symbol_to_find is None:
        return net_qty

    if ret is None:
        return net_qty  # Return None if the positions are not available

    for position in ret:
        instname = position.get('dname', '')
        if instname and symbol_to_find in instname:
            net_qty_str = position.get('netqty', None)  # Get netqty as a string
            if net_qty_str is not None and net_qty_str.isdigit():
                net_qty = int(net_qty_str)
                break  # Exit the loop once we find the symbol

    return net_qty










#
# autologin()
# get_position_detail()
# symstring=f"NIFTY 07SEP23 16650 CE"
# get_option_detail(tradingsymbol=symstring)
#
# short_order(tradingsymbol=symstring,quantity=50,Product_Type="NRML")
# buy_order()
# get_ltp()
# get_historical_data()