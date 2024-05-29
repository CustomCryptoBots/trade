# deprecated code workaround
import collections
from collections import abc
collections.MutableMapping = abc.MutableMapping
collections.Mapping = abc.Mapping
collections.Sequence = abc.Sequence
collections.Callable = abc.Callable

# imports
from coinbase.wallet.client import Client as cbc
import cbpro
import time
from datetime import datetime


class trade:
    
    
    # class variables
    api = open("/home/dev/code/dat/api.txt", "r").read().splitlines()
    cb_client = cbc(api[0], api[1])
    cbp = cbpro.PublicClient()
    wirePath = "/home/dev/code/tmp/" + str(datetime.now().strftime("%Y-%m-%d %H-%M-%S")) + ".txt"   
    names = []
    
    
    # initializer
    def __init__(self):
        start_time = time.time()    # track runtime
    
        self.getWallets()           # populate names[]
    
        # check price to identify viable assets
        invalid = 0
        for n in self.names:
            self.output(n + " ")
            try:
                ticker = self.getPrice(n)
                self.output(str(ticker['price']) + "\n")                
                                
            except:
                invalid += 1
                self.output("invalid\n")

        self.output("\n" + str(invalid) + " invalid wallets\n\n")                     
        
        end_time = time.time()
        sec = end_time - start_time
        self.output("\nRuntime\n")
        self.output(str(round(sec, 2)) + " seconds\n")
        self.output(str(round((sec / 60), 2)) + " minutes\n")
        
    
    # streamline output
    def output(self, message):
        wire = open(self.wirePath, "a")
        wire.write(message)
        wire.close()


    # get all coinbase wallet names
    def getWallets(self):
        try:
            account = self.cb_client.get_accounts(limit = 300)

        except Exception as e:
            self.output(str(e) + "\n\n")
    
        # populate names class variable
        self.names = [wallet['name'].replace(" Wallet", "") for wallet in account.data]
            
    
    # check live price
    def getPrice(self, asset):
        try:
            asset += "-USD"
            ticker = self.cbp.get_product_ticker(product_id = asset)
            return ticker
        
        except Exception as e:
            self.output(str(e) + "\n\n")


# void main
_new = trade()
