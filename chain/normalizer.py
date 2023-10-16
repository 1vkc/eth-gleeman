import enum
import os
from web3 import Web3
from chain.decoder import ABIDecoder
from chain.tracer import visit_trace_frame
from typing import Callable, Dict
from web3.datastructures import (
    AttributeDict,
)
import json
from chain.token import TokenProvider

alias = ['argonaut','atlas','centurion','chronos','dragoon','exodus','galahad','goliath','griffin','hyperion','inferno','kraken','lynx','manticore','nomad','nova','oblivion','onyx','orion','paladin','phantom','phoenix','pulsar','pyro','quantum','quasar','raptor','razor','reaper','sabre','scorpio','sentinel','seraph','spartan','specter','spectre','storm','striker','templar','titan','triton','valkyrie','vanguard','vector','vortex','vulcan','wraith','zenith','zephyr','zodiac']
tokenProvider = TokenProvider()
decoder = ABIDecoder()

class AddressType(enum.Enum):
    UNKOWN = enum.auto()
    EOA = enum.auto()
    CONTRACT = enum.auto()
    ERC20 = enum.auto()
    NFT = enum.auto()

class NormalizedAddress:
    _address: str
    _alias: str
    _type: AddressType

    def __init__(self, addr: str, alias: str, t: AddressType = AddressType.UNKOWN):
        self._address = addr
        self._alias = alias
        self._type = t

    def address_type(self):
        return self._type

    def string(self):
        return self._alias


class ContractAddress(NormalizedAddress):
    def __init__(self, addr: str, alias: str):
        super().__init__(addr, alias, AddressType.CONTRACT)


    def string(self):
        return f"contract_{self._alias}"
    
class ERC20Address(NormalizedAddress):
    _symbol: str
    _decimal: int

    def __init__(self, addr: str, alias: str, symbol: str, decimal: int):
        super().__init__(addr, alias, AddressType.ERC20)
        self._symbol = symbol
        self._decimal = decimal

    def string(self):
        return f"token_{self._symbol}"

class AddressNormalizer:
    _w3: Web3
    _addrs = {}

    def __init__(self, w3: Web3):
        self._w3 = w3

    # hack is contract check
    def add(self, addr: str):
        if type(addr) is not str:
            return
        
        addr = addr.lower()
        if addr not in self._addrs:
            self._addrs[addr] = self.__detect_addr(addr)

    def __detect_addr(self, addr: str) -> NormalizedAddress:
        a = alias[len(self._addrs)]
        
        token = tokenProvider.erc20(addr)
        if token:
            return ERC20Address(addr, a, token[0], token[1])
        
        # token = tokenProvider.nft(addr)
        # if token:
        #     return NormalizedAddress(addr, a, AddressType.EOA)

        # code = self._w3.eth.get_code(Web3.to_checksum_address(addr))
        # if code != b'':
        # if isContract:
        #     return ContractAddress(addr, a)
        
        return NormalizedAddress(addr, a, AddressType.EOA)

    def get(self, addr: str) -> NormalizedAddress:
        if type(addr) is not str:
            return addr
        
        addr = addr.lower()
        if addr in self._addrs:
            return self._addrs[addr]
        else:
            return NormalizedAddress(addr, addr[:10])
        
class TraceNormalizer:
    _w3: Web3
    _trace: AttributeDict
    _address_normalizer: AddressNormalizer


    def __init__(self, w3: Web3, trace):
        self._w3 = w3
        self._trace = trace
        self._address_normalizer = AddressNormalizer(w3)
    
    def visit_trace(self):
        def normalize_to(trace: AttributeDict):
            self._address_normalizer.add(trace["from"])
            self._address_normalizer.add(trace["to"])
        visit_trace_frame(self._trace, normalize_to)

        def normalize_param(trace: AttributeDict):
            decoded = decoder.parse_trace(trace.input)
            if decoded:
                abi = decoded[0]
                param = decoded[1]

                # print(decoded)
                for p in abi["inputs"]:
                    if p["type"] == "address":
                        param_name = p["name"]
                        self._address_normalizer.add(param[param_name])
        visit_trace_frame(self._trace, normalize_param)

        def parse_trace(trace: AttributeDict):
            _from = self._address_normalizer.get(trace['from']).string()
            _to = self._address_normalizer.get(trace['to']).string()
            _value = int(trace.value, 0)
            if trace.input == "0x":
                print(f"{_from}{f' {{{_value} ether}}' if _value != 0 else '' } => {_to} ")
                return

            decoded = decoder.parse_trace(trace.input)
            method = trace.input[:10]

            if decoded:
                abi = decoded[0]
                param = decoded[1]
                param_list = [f"{p}={self._address_normalizer.get(v).string() if type(v) is str else ('bytes' if type(v) is bytes else v)}" for p, v in param.items()]

                # method = prefix + "." + abi["name"]
                method = abi["name"]
                print(f"{_from}{f' {{{_value} ether}}' if _value != 0 else '' } => {_to}.{method}({','.join(param_list)})")
            else:
                print(f"{_from}{f' {{{_value} ether}}' if _value != 0 else '' } => {_to}.{method}")

            return method

        visit_trace_frame(self._trace, parse_trace)
