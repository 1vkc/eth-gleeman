import os
import typing
from web3 import Web3, constants
from web3.types import ABI, ABIFunction, ABIEvent
from web3._utils.abi import filter_by_type
from web3._utils.normalizers import normalize_abi, BASE_RETURN_NORMALIZERS
from web3._utils.contracts import decode_transaction_data
from web3._utils.encoding import to_4byte_hex
from eth_utils import function_abi_to_4byte_selector, encode_hex

class ABIDecoder:
    contractABI: typing.Dict[str, typing.Dict[str, ABIFunction]]
    functionABI: typing.Dict[str, ABIFunction]

    def __init__(self):
        self.contractABI = {}
        self.functionABI = {}

        w = os.walk("data/abi")
        for path, _, fs in w:
            for fp in fs:
                address = os.path.splitext(fp)[0]
                with open(os.path.join(path, fp)) as f:
                    abi_json = f.read()
                    if not abi_json:
                        print(address, "empty")
                        continue
                    self._load_abi(address, abi_json)


    def _load_abi(self, address: str, abi_json: str):
        try:
            abis: ABI = normalize_abi(abi_json)
            fns_abis = filter_by_type("function", abis)
        except Exception as e:
            print(address, e)
            raise e

        _con_abis = {}

        for abi in fns_abis:
            fbyte = encode_hex(function_abi_to_4byte_selector(abi))
            _con_abis[fbyte] = abi
            self.functionABI[fbyte] = abi
        
        self.contractABI[address] = _con_abis


    def parse_tx_trace(self, num: int, hash: str):
        trace_path = f"data/trace/{num}/{hash}.json"

    def parse_trace(self, call: str)-> (ABI, typing.Dict[str, typing.Any]):
        fbyte = call[:10]

        if fbyte in self.functionABI:
            abi = self.functionABI[fbyte]
            return abi, decode_transaction_data(abi, call, BASE_RETURN_NORMALIZERS)