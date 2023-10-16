import os
from web3 import Web3
from web3.tracing import Tracing
from web3.datastructures import (
    AttributeDict,
)
import pandas as pd 
from typing import Callable
from etherscan.contracts import Contract

# def visit_trace_frame_p(trace: AttributeDict, handle_trace: Callable, call_prefix):
#     if not "type" in trace:
#         print(Web3.to_json(trace))
#         return

#     if not (trace.type == "CALL" or trace.type == "DELEGATECALL") or trace.input == "0x":
#         return
    
#     if trace.type == "CALL":
#         call_prefix = handle_trace(trace, call_prefix)

#     if "calls" in trace:
#         for call in trace.calls:
#             visit_trace_frame_p(call, handle_trace, call_prefix)

def visit_trace_frame(trace: AttributeDict, handle_trace: Callable):
    if not "type" in trace:
        print(Web3.to_json(trace))
        return

    if not (trace.type == "CALL" or trace.type == "DELEGATECALL"):
        return 

    if trace.type == "CALL":
        handle_trace(trace)

    if "calls" in trace:
        for call in trace.calls:
            visit_trace_frame(call, handle_trace)

class TxTracer:
    tracer_config = { "tracer": "callTracer" }
    etherscan_no_abi: set

    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(os.environ["ETHER_HTTP_URL"]))

        no_abi_df = pd.read_csv("data/noabi.csv", header=None)
        self.etherscan_no_abi = set(no_abi_df[no_abi_df.columns[0]].to_numpy())


    def get_abi(self, add: str):
        # address = Web3.to_checksum_address(add)
        address = add.lower()
        abi_file_path = f"data/abi/{address}.json"

        if address in self.etherscan_no_abi:
            return None

        if os.path.exists(abi_file_path):
            with open(abi_file_path, 'r') as f:
                abi = f.read()
                return abi

        contract = Contract(address=address, api_key = os.environ["ETHERSCAN_KEY"])

        try:
            abi = contract.get_abi()
        except Exception as err:
            print(address, err)
            self.etherscan_no_abi.add(address)
        else:
            if not abi:
                print(f"get empty abi from etherscan {address}")
                return None
            with open(abi_file_path, 'x') as f:
                f.write(abi) 
            return abi

        return None

    def trace_block(self, num: int):
        print(f"tracing block {num}")
        os.makedirs(f"data/trace/{num}", exist_ok=True)

        tx_hashs = self.w3.eth.get_block(num)
        block_trace = self.w3.manager.request_blocking("debug_traceBlockByNumber", [Web3.to_hex(num), self.tracer_config])

        for index, tx_trace in enumerate(block_trace):

            tx_hash = tx_hashs.transactions[index].hex()
            tx_result = tx_trace.result

            tx_json = Web3.to_json(tx_result)

            with open(f"data/trace/{num}/{tx_hash}.json", mode='x') as f:
                f.write(tx_json)

            def parse_trace(trace):
                self.get_abi(trace.to)

            visit_trace_frame(tx_result, parse_trace)

        self._save_etherescan_abi()

    def back_fill_block(self, start: int, end: int):
        for num in range(start, end):
            self.trace_block(num)

    def _save_etherescan_abi(self):
        no_abi_df = pd.DataFrame(self.etherscan_no_abi)
        no_abi_df.to_csv("data/noabi.csv", index=False, header=None)