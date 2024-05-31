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
    
        # asset prices                                      # keep this until self.include
        prices = set()                                      # is finalized    
        for n in self.include:
            try:
                ticker = self.getPrice(n)
                if ticker:
                    prices.add(f"{n} {ticker['price']}")                
            except Exception as e:
                self.output_buffer.append(f"{n} Invalid Price\n\n")
        self.output_buffer.append(f"Include {len(self.include)}\n{prices}\n\n")

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


    # match known assets with all available
    # via api key and check for new wallets
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
            self.output(f"{str(e)}\n\n")
            return
        
        # check for new/removed assets
        names = {wallet['name'].replace(" Wallet", "") for wallet in account.data}
        new_cryptos = names - self.include - exclude
        removed_cryptos = self.include - names 
        
        if new_cryptos:
            self.output_buffer.extend([f"### NEW CRYPTO -> {n} ###\n\n" for n in new_cryptos])
        if removed_cryptos:
            self.output_buffer.extend([f"### REMOVED CRYPTO -> {n} ###\n\n" for n in removed_cryptos])
        self.output_buffer.append(f"Exclude {len(exclude)}\n{exclude}\n\n")


    # live price
    def getPrice(self, asset):
        try:
            asset += "-USD"
            ticker = self.cbp.get_product_ticker(product_id = asset)
            return ticker    
        except Exception as e:
            self.output_buffer.append(f"{str(e)}\n\n")
            return None


# void main
_new = Trade()
