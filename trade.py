import collections
from collections import abc
collections.MutableMapping = abc.MutableMapping
collections.Mapping = abc.Mapping
collections.Sequence = abc.Sequence
collections.Callable = abc.Callable
from coinbase.wallet.client import Client as cbc
import cbpro
import time
from datetime import datetime
import csv
import pandas as pd


class Trade:
    def __init__(self):  
        start_time = time.time()    # track runtime
        
        # instance variables
        with open("/home/dev/code/dat/api.txt", "r") as api_file:
            self.api = api_file.read().splitlines()
        self.wirePath = "/home/dev/code/tmp/" + str(datetime.now().strftime("%Y-%m-%d %H-%M-%S")) + ".txt"
        self.cb_client = cbc(self.api[0], self.api[1])      # coinbase api connection
        self.cbp = cbpro.PublicClient()                     # live price data
        self.include = set()                                # available assets
        self.output_buffer = []                             # for all output
        
        self.syncWallets()                                  # match input file with coinbase api
    
        # asset prices and historical trading data
        self.output_buffer.append(f"name,mean,median,mode,std,var,min,max,range,iqr,vol,days\n")
        prices = set()    
        for n in self.include:
            try:
                ticker = self.getPrice(n)
                #self.output_buffer.append(f"{n}\n{ticker}\n\n")
                if ticker:                                  # get price, candlestick and stats info
                    prices.add(f"{n} {ticker}")                
                    df = self.getHistoric(n)
                    stats = self.timeDiff(df) 
                    mean = stats['mean'] 
                    median = stats['median']
                    mode = stats['mode']
                    std = stats['std']
                    var = stats['variance']
                    minn = stats['min']
                    maxx = stats['max']
                    rnge = stats['range'] 
                    iqr = stats['iqr']
                    vol = round(sum(df['Volume']), 0)
                    length = round((df['Date'].max() - df['Date'].min()).total_seconds() / (24 * 3600), 2)      # convert to days
                    self.output_buffer.append(f"{n},{mean},{median},{mode},{std},{var},{minn},{maxx},{rnge},{iqr},{vol},{length}\n")
            except Exception as e:
                self.output_buffer.append(f"{e}\n\n")
        #self.output_buffer.append(f"Include {len(self.include)}\n{prices}\n\n")
        end_time = time.time()
        sec = end_time - start_time
        self.output_buffer.append(f"\nRuntime\n")
        self.output_buffer.append(f"{round(sec, 2)} seconds\n")
        self.output_buffer.append(f"{round((sec / 60), 2)} minutes\n")
        self.output(''.join(self.output_buffer))            # only one write for output_buffer
        
    
    # streamline output
    def output(self, message):
        with open(self.wirePath, "a") as wire:
            wire.write(message)


    # match known assets with all available via
    # api key and check asset availability changes
    def syncWallets(self):     
        # read from input file
        exclude = set()
        with open("/home/dev/code/dat/inp.txt", "r") as infile:
            reader = csv.reader(infile)
            for row in reader:
                if row[1] == "0":           
                    self.include.add(row[0])
                elif row[1] == "1":
                    exclude.add(row[0])
        
        # get all wallets from coinbase api
        try:
            account = self.cb_client.get_accounts(limit = 300)
        except Exception as e:
            #self.output_buffer.append(f"{str(e)}\n\n")
            return
        
        # check for new/removed assets
        names = {wallet['name'].replace(" Wallet", "") for wallet in account.data}
        new_cryptos = names - self.include - exclude
        removed_cryptos = self.include - names 
        
        if new_cryptos:
            self.output_buffer.extend([f"### NEW CRYPTO -> {n} ###\n\n" for n in new_cryptos])
        if removed_cryptos:
            self.output_buffer.extend([f"### REMOVED CRYPTO -> {n} ###\n\n" for n in removed_cryptos])
        #self.output_buffer.append(f"Exclude {len(exclude)}\n{exclude}\n\n")

    
    # authenticated price check
    def getPrice(self, asset):
        try:
            currency_pair = f"{asset}-USD"
            price = self.cb_client.get_spot_price(currency_pair = currency_pair)
            return price['amount']
        except Exception as e:
            #self.output_buffer.append(f"{asset}\n{e}\n\n")
            return None


    # candlestick data
    def getHistoric(self, asset):
        try:
            assetUSD = asset + "-USD"
            # 15 minute granularity * 300 rows = 3.125 days
            raw = self.cbp.get_product_historic_rates(product_id = assetUSD, granularity = 900)
            df = pd.DataFrame(raw, columns = ['Date', 'Low', 'High', 'Open', 'Close', 'Volume'])
            df = df.iloc[::-1].reset_index(drop = True)               # chronological order
            df['Date'] = pd.to_datetime(df['Date'], unit = 's')       # make readable
            return df
        except Exception as e:
            #self.output_buffer.append(f"{str(e)}\n\n")
            return None


    # analyze time difference reporting issue
    def timeDiff(self, df):
        # in minutes between consecutive rows
        df['TimeDiff'] = (df['Date'] - df['Date'].shift(1)).dt.total_seconds() / 60.0
        
        # drop the first row because it has NaN in 'TimeDiff'
        df = df.iloc[1:].reset_index(drop=True)
        
        # calculate statistical information
        stats = {
            'mean': round(df['TimeDiff'].mean(), 2),
            'median': round(df['TimeDiff'].median(), 2),
            'mode': df['TimeDiff'].mode().iloc[0] if not df['TimeDiff'].mode().empty else None,
            'std': round(df['TimeDiff'].std(), 2),
            'variance': round(df['TimeDiff'].var(), 2),
            'min': df['TimeDiff'].min(),
            'max': df['TimeDiff'].max(),
            'range': df['TimeDiff'].max() - df['TimeDiff'].min(),
            'iqr': round(df['TimeDiff'].quantile(0.75) - df['TimeDiff'].quantile(0.25), 2)
        }

        return stats


# void main
_new = Trade()
