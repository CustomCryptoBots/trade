# imports
from coinbase.wallet.client import Client as cbc
import time
from datetime import datetime


class trade:
    
    # class variables
    api = open("/home/dev/code/dat/api.txt", "r").read().splitlines()
    cb_client = cbc(api[0], api[1])
    wirePath = "/home/dev/code/tmp/" + str(datetime.now().strftime("%Y-%m-%d %H-%M-%S")) + ".txt"
    names = []
    
    
    # initializer
    def __init__(self):
        start_time = time.time()    # track runtime
        
        self.getWallets()             
        
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
    
        # make list and output
        self.names = [wallet['name'].replace(" Wallet", "") for wallet in account.data]
        [self.output(n + "\n") for n in self.names]


# void main
_new = trade()
