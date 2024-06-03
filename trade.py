from coinbase.wallet.client import Client as cbc
import time
from datetime import datetime
import csv
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor


class Trade:
    def __init__(self):  
        start_time = time.time()                            # track runtime
        
        # instance variables
        with open("/home/dev/code/dat/api.txt", "r") as api_file:
            self.api = api_file.read().splitlines()
        self.wirePath = "/home/dev/code/tmp/" + str(datetime.now().strftime("%Y-%m-%d %H-%M-%S")) + ".txt"
        self.cb_client = cbc(self.api[0], self.api[1])      # coinbase api connection
        self.include = set()                                # available assets
        self.output_buffer = []                             # for all output
        self.output_buffer.append(f"name,mean,median,mode,std,var,min,max,range,iqr,vol,days\n")
        
        # sync wallets then batch process candlestick data api calls
        self.syncWallets()
        with ThreadPoolExecutor(max_workers = 10) as executor:
            futures = [executor.submit(self.getHistoric, asset) for asset in self.include]
            for future in futures:
                asset, df = future.result()
                if df is not None:
                    self.timeDiff(asset, df)
        
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
            self.output_buffer.append(f"{str(e)}\n\n")
            return
        
        # check for new/removed assets
        names = {wallet['name'].replace(" Wallet", "") for wallet in account.data}
        new_cryptos = names - self.include - exclude
        removed_cryptos = self.include - names 
        
        if new_cryptos:
            self.output_buffer.extend([f"### NEW CRYPTO -> {n} ###\n\n" for n in new_cryptos])
        if removed_cryptos:
            self.output_buffer.extend([f"### REMOVED CRYPTO -> {n} ###\n\n" for n in removed_cryptos])

    
    # authenticated price check
    def getPrice(self, asset):
        try:
            currency_pair = f"{asset}-USD"
            price = self.cb_client.get_spot_price(currency_pair = currency_pair)
            return price['amount']
        except Exception as e:
            self.output_buffer.append(f"{asset}\n{e}\n\n")
            return None


    # candlestick data
    def getHistoric(self, asset):
        try:
            assetUSD = asset + "-USD"
            url = f"https://api.pro.coinbase.com/products/{assetUSD}/candles"
            
            # send get request to the api
            response = requests.get(url, params = {'granularity': 900})
            response.raise_for_status()                             # exception for HTTP errors
            raw = response.json()
            df = pd.DataFrame(raw, columns = ['Date', 'Low', 'High', 'Open', 'Close', 'Volume'])
            df = df.iloc[::-1].reset_index(drop = True)             # chronological order
            df['Date'] = pd.to_datetime(df['Date'], unit = 's')     # make date readable
            return asset, df
        except requests.exceptions.RequestException as e:
            self.output_buffer.append(f"{str(e)}\n\n")
            return None


    # analyze time difference reporting issue
    def timeDiff(self, asset, df):
        # in minutes between consecutive rows
        df['TimeDiff'] = (df['Date'] - df['Date'].shift(1)).dt.total_seconds() / 60.0
        # drop the first row because it has NaN in 'TimeDiff'
        df = df.iloc[1:].reset_index(drop = True)

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
            'iqr': round(df['TimeDiff'].quantile(0.75) - df['TimeDiff'].quantile(0.25), 2),
            'vol': round(sum(df['Volume']), 0),
            'length': round((df['Date'].max() - df['Date'].min()).total_seconds() / (24 * 3600), 2)  # days
        }

        self.output_buffer.append(f"{asset},{stats['mean']},{stats['median']},{stats['mode']},{stats['std']},{stats['variance']},{stats['min']},{stats['max']},{stats['range']},{stats['iqr']},{stats['vol']},{stats['length']}\n")


# void main
_new = Trade()
