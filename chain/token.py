import json
import typing
from web3 import Web3

class SingleToken:
    address: str
    symbol: str
    decimals: int

class TokenProvider:
    localList:typing.Dict[int, typing.Dict[str,SingleToken]] #chainId-address-token

    def __init__(self):
        with open("data/tokenlist/uniswapToken.json") as listFile:
            rawJson = listFile.read()
            tokenList = json.loads(rawJson)
            listArray = tokenList["tokens"]
            
            self.localList = dict()
            for rawToken in listArray:
                specifiedChainList = self.localList.get(rawToken["chainId"])
                
                singleToken = SingleToken()
                singleToken.address = Web3.to_checksum_address(rawToken["address"])
                singleToken.decimals = rawToken["decimals"]
                singleToken.symbol = rawToken["symbol"]
                if specifiedChainList is None:
                    self.localList[rawToken["chainId"]] = {singleToken.address:singleToken}
                else:
                    self.localList[rawToken["chainId"]].update({singleToken.address:singleToken})


    def erc20(self, address:str):
        token =  self.fetchToken(1, address)
        if token:
            return token.symbol, token.decimals
    
    def fetchToken(self, chainId:int, address:str):
        specifiedChainList = self.localList.get(chainId)
        if specifiedChainList != None:
            token = specifiedChainList.get(Web3.to_checksum_address(address))
            if token == None:
                return None
            return token
        else:
            #todo fetch from chain
            return None