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
        self.api = open("/home/dev/code/dat/api.txt", "r").read().splitlines()  
        self.wirePath = "/home/dev/code/tmp/" + str(datetime.now().strftime("%Y-%m-%d %H-%M-%S")) + ".txt"
        self.cb_client = cbc(self.api[0], self.api[1])      # coinbase api connection
        self.cbp = cbpro.PublicClient()                     # live price data
        self.include = []                                   # available assets

        self.syncWallets()          # match input file with coinbase api
    
        # asset prices
        prices = []
        for n in self.include:
            try:
                ticker = self.getPrice(n)
                prices.append(n + " " + str(ticker['price']))                
            except:
                self.output(self.output(n + " " + str(e) + "\n\n"))
        
        self.output("Prices\n" + str(prices) + "\n\n")

        end_time = time.time()
        sec = end_time - start_time
        self.output("\nRuntime\n")
        self.output(str(round(sec, 2)) + " seconds\n")
        self.output(str(round((sec / 60), 2)) + " minutes\n")
        
    
    # streamline output
    def output(self, message):
        with open(self.wirePath, "a") as wire:
            wire.write(message)


    # match known assets with all available
    # via api key and check for new wallets
    def syncWallets(self):
        exclude = []
        
        # read from input file
        with open("/home/dev/code/dat/inp.txt", "r") as infile:
            reader = csv.reader(infile)
            for row in reader:
                if row[1] == "0":           
                    self.include.append(row[0])
                elif row[1] == "1":
                    exclude.append(row[0])
        
        # get all wallets from coinbase api
        try:
            account = self.cb_client.get_accounts(limit = 300)
        except Exception as e:
            self.output(str(e) + "\n\n")
   
        # check for new assets
        names = [wallet['name'].replace(" Wallet", "") for wallet in account.data]
        for n in names:
            if n not in self.include and n not in exclude:
                self.output("### NEW CRYPTO -> " + n + " ###\n\n") 
        
        self.output("Exclude\n" + str(exclude) + "\n\n")


    # live price
    def getPrice(self, asset):
        try:
            asset += "-USD"
            ticker = self.cbp.get_product_ticker(product_id = asset)
            return ticker    
        except Exception as e:
            self.output(str(e) + "\n\n")
            return None


# void main
_new = Trade()
