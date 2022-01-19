MERGE_AND_EXPORT = True # if false, no merging and excel functions will be applied
DEV_MODE = False # if False, the input data will be moved to temp file once process is finished;

# if a new netwrok to be added, the following list/dicts has to be adjusted as well, i.e.:
# 1) network_list, 2) dict_links, and 3) _dict_colums_float
# also addresses of stable coins has to be added in config_stables.py 
networks_list = ["ETH", "BNB", "MATIC", "AVAX", "FTM"]

dict_links = {
    "ETH": "https://etherscan.io/tx/",
    "BNB": "https://bscscan.com/tx/",
    "MATIC": "https://polygonscan.com/tx/",
    "AVAX": "https://snowtrace.io/tx/",
    "FTM": "https://ftmscan.com/tx",
}

# The following dictionary could be a single dynamic list/dict which could be aplied adjust_list/adjust_dict  
#  function as they are as well in the following lists/dictionaries, but "Historical Price/Eth" is not in 
#  capital as the remaingn networks. Laziness won. 
_dict_colums_float = {
    "ETH": ["Value_IN({})", "Value_OUT({})", "TxnFee({})", "TxnFee(USD)", "Historical $Price/Eth"],
    "BNB": ["Value_IN({})", "Value_OUT({})", "TxnFee({})", "TxnFee(USD)", "Historical $Price/BNB"],
    "MATIC": ["Value_IN({})", "Value_OUT({})", "TxnFee({})", "TxnFee(USD)", "Historical $Price/MATIC"],
    "AVAX": ["Value_IN({})", "Value_OUT({})", "TxnFee({})", "TxnFee(USD)", "Historical $Price/MATIC"],
    "FTM": ["Value_IN({})", "Value_OUT({})", "TxnFee({})", "TxnFee(USD)", "Historical $Price/MATIC"],
}

_columns_to_be_moved = ["{}_IN", "{}_OUT", "{}_BALANCE", "{}_USD_PRICE", "Method"]
_columns_to_be_merged = _columns_to_be_moved + ["Txhash", "UnixTimestamp", "TxnFee({})", "TxnFee(USD)"]
_columns_final_order = [
    "TokenSymbol", "A", "TokenDirection", "UnixTimestamp", "Value", "TokenBalanceBefore", "TokenBalanceAfter", 
    "{}_IN", "{}_OUT", "{}_BALANCE", "{}_USD_PRICE", "Method", "EVENT", "USD_PRICE", "USD_STATE", "STATUS", 
    "Txhash",
    ]

delete_columns_tokens = ["DateTime"]
delete_columns_txs = delete_columns_tokens + ["Blockno"]
not_consired_as_swap = ["Deposit"]

EVENTS = {
    0: "PURCHASE", 
    1: "SALE",
    2: "EXPENSE",
    3: "INCOME",
    4: "OUTCOME",
    5: "NOT DEFINED",
}

dic_methods = {
    "IN": {
        "taxable_events": ["swap"],
        "non_taxable_events": ["approve", "approval", "withdraw", "claim", "unstake", "liquidity", "Cancel Auction"], 
        # NOTE: claim is not considered as a taxable event;
    },
    "OUT": {
        "taxable_events": ["swap"],
        "non_taxable_events": ["approve", "approval", "deposit", "stake", "liquidity", "Create Auction"], 
    }    
}

_dict_columns_to_hide = {
    "{}_BALANCE": "J", 
    "Txhash": "Q",
    "From": "R",
    "To": "S",
    "ContractAddress": "T",
    "TokenName": "U",
    "TxnFee(ETH)": "V",
    "TxnFee(USD)": "W",
}

# used for excel adjustment, see helper_excel.py 
dict_columns_width = {
    "TokenSymbol": ["A", 8, True],
    "A": ["B", 2, False],
    "UnixTimestamp": ["D", 10, False],
    "EVENT": ["M", 11, True],
    "USD_PRICE": ["N", 14, True],
    "USD_STATE": ["O", 18, True],
    "STATUS": ["P", 11, True],
}

_dict_headers_rename = {
    "TokenSymbol": "Token Symbol",
    "TokenDirection": "Token Direction",
    "UnixTimestamp": "Unix Timestamp",
    "TokenBalanceBefore": "Token Balance Before",
    "TokenBalanceAfter": "Token Balance After",
    "{}_IN": "{} IN",
    "{}_OUT": "{} OUT",
    "{}_USD_PRICE": "{} USD",
    "EVENT": "Event",
    "USD_PRICE": "USD price",
    "USD_STATE": "USD state",
    "STATUS": "Status",
    "HYPERLINK": "Hyperlink",
}


def adjust_list(cols, network):
    """
    Replace missing data {} in a list by the name of the network
    """
    col_out = []
    for col in cols:
        out = col.format(network)
        col_out.append(out)

    return col_out


def adjust_dict(dict_in, network):
    """
    Replace missing data {} in a dictionary by the name of the network
    """
    dict_out = {}
    for key, val in dict_in.items():
        new_key = key.format(network)
        new_value = val.format(network)
        dict_out[new_key] = new_value
    return dict_out


def main():
    pass


if __name__ == "__main__":
    main()