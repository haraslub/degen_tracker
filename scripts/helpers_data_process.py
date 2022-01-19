import numpy as np
import pandas as pd
import math

from helpers_general import (get_duplicated_txhashes, is_item_in_list)
from config import EVENTS, dic_methods
from config_stables import dict_stables


def get_token_direction(df, address):
    """
    Add erc20 token direction (in/out) to a newly created column 'TokenDirection' in data frame (df). Address has to be erc20
    owner and it is used to check if tokens were sent to/from the owner address.

    Args:
        df (pandas.DataFrame):
        address (string):
    Returns:
        df (pandas.DataFrame): the data frame with a newly created colum 'TokenDirection'

    """
    print("Getting tokens' directions")

    # create column and set initial values NaN
    df["TokenDirection"] = np.NaN
    address = address.lower()

    for index, row in df.iterrows():
        if address in row["From"]:
            direction = "OUT"
        elif address in row["To"]:
            direction = "IN"
        else:
            direction = "None"
        df.loc[index, "TokenDirection"] = direction

    return df


def get_token_balance(df):
    """
    Get and assign token balance of the given erc20 token.
    Args:
        df (pandas DataFrame): the df to be added token balances
    Returns:
        df (pandas DataFrame): the same df extended by columns "TokenBalanceBefore" and "TokenBalanceAfter"
    """
    
    print("Getting tokens' balances")
    # create empty columns and set initial values
    df["TokenBalanceBefore"] = np.NaN
    df["TokenBalanceAfter"] = np.NaN
    # change value to float
    df["Value"] = df["Value"].astype(float)

    for index, row in df.iterrows():

        contract_address = row["ContractAddress"]
        unix_timestamp = row["UnixTimestamp"]
        
        # If token direction is OUT, change the Value to negative
        if row["TokenDirection"] == "OUT":
            df.loc[index, "Value"] = row["Value"] * -1
        value = df.loc[index, "Value"]

        df_fil = df[(df.ContractAddress == contract_address) & (df.UnixTimestamp <= unix_timestamp)]

        # Token Balance After
        balance_after = df_fil["Value"].sum()
        # Check if the balance calculated is closed to zero, if so, set to zero:
        if math.isclose(0, balance_after, abs_tol=1E-10):
            balance_after = 0
        # Assign token balance after to data
        df.loc[index, "TokenBalanceAfter"] = balance_after
        
        # Token Balance Before:
        if index > 0:
            df.loc[index, "TokenBalanceBefore"] = df_fil["Value"].sum() - value
        else:
            df.loc[index, "TokenBalanceBefore"] = 0
        
    return df


def get_eth_io_and_balance(df, network):

    print("Getting {} input/output, balances, prices".format(network))
    df.sort_values(by=["UnixTimestamp"], inplace=True)

    # create new columns
    col_IN = "{}_IN".format(network)
    col_OUT = "{}_OUT".format(network)
    col_BALANCE = "{}_BALANCE".format(network)
    col_USD_PRICE = "{}_USD_PRICE".format(network)

    df[col_IN] = np.NaN
    df[col_OUT] = np.NaN
    df[col_BALANCE] = np.NaN
    df[col_USD_PRICE] = np.NaN

    for index, row in df.iterrows():
        # get eth input transaction:
        df.loc[index, col_IN] = np.nanmax(
            [row["Value_IN({})_x".format(network)], row["Value_IN({})_y".format(network)]])
        # get eth output transactions:
        df.loc[index, col_OUT] = np.nanmax(
            [row["Value_OUT({})_x".format(network)], row["Value_OUT({})_y".format(network)]])
        # get eth balance at the time:
        # NOTE: as NFT transactions are not included, the balance is not calculated correctly
        if index == 0:
            df.loc[index, col_BALANCE] = df.loc[index, col_IN]
        else:
            df.loc[index, col_BALANCE] = df.loc[index-1, col_BALANCE] + df.loc[index, col_IN] - df.loc[index, col_OUT] - np.nanmax([row["TxnFee({})".format(network)], 0])
        # get eth usd price at the time of transaction
        # NOTE all EVM chains has capital ticker in all columns, but in the case of ETH some ticker is capital some not,
        #   thus I needed define network_adjusted variable to handle it
        network_adjusted = network 
        if network == "ETH":
            network_adjusted = network.capitalize()
        if math.isnan(row["Historical $Price/{}".format(network_adjusted)]) == False:
            df.loc[index, col_USD_PRICE] = row["Historical $Price/{}".format(network_adjusted)]
        else:
            df.loc[index, col_USD_PRICE] = ""


def extract_usd_price_of_eth_from_column(df, network):
    """
    Extract USD price of ETH (or other EVM chains) from the header and if there is missing value in Historical Price column,
    extracted value is placed there
    """
    print("Extracting price of the ETH")
    col = df.columns[pd.Series(df.columns).str.startswith("CurrentValue") == True][0]
    price = float(col.split("$", 1)[1].split("/")[0])
    print("... price extracted: {}".format(price))
    
    # NOTE all EVM chains has capital ticker in all columns, but in case of ETH some ticker is capital some not,
    #   thus I needed define network_adjusted variable
    network_adjusted = network
    if network == "ETH":
        network_adjusted = network.capitalize()

    # print("Replacing empty values of ETH price by the price extracted.")    
    for index, row in df.iterrows():
        if row["Historical $Price/{}".format(network_adjusted)] == "":
            print("... price extracted: {} USD/{}".format(price, network))
            df.loc[index, "Historical $Price/{}".format(network_adjusted)] == price


def get_event(df, network):
    """
    Assign event based on the several conditions.
    """
    print("Getting events")

    df["EVENT"] = np.NaN
    duplicated_hashes = get_duplicated_txhashes(df, "Txhash")

    df.sort_values(by=["UnixTimestamp"], inplace=True)
    
    for index, row in df.iterrows():
        # if not a token, NEXT ITERATION
        if pd.isnull(row["ContractAddress"]):
            continue
        # set to event initial value
        event = EVENTS[5] # EVENT = NOT DEFINED

        if row["TokenDirection"] == "IN":
            if (row["Txhash"] in duplicated_hashes) & is_item_in_list("swap", [str(row["Method"])]):
                event = EVENTS[0] # EVENT = PURCHASE
            else:
                event = evaluate_tx(row, "IN", network)

        elif row["TokenDirection"] == "OUT":
            if (row["Txhash"] in duplicated_hashes) & is_item_in_list("swap", [str(row["Method"])]):
                event = EVENTS[1] # EVENT = SALE
            else:
                event = evaluate_tx(row, "OUT", network)
        
        df.loc[index, "EVENT"] = event


def evaluate_tx(row, direction, network):
    """
    Get EVENT (EVENT defined in config from a transaction. This function is part of
    function 'get_event'
    """
    # DEFINE OPPOSITE DIRECTION (NEEDED FOR CHECK NO 1)
    if direction == "IN":
        opposite = "OUT"
    elif direction == "OUT":
        opposite = "IN"
    else:
        return "MISSING INPUT DATA (DIRECTION OF TXs)"

    #1 CHECK IF ETH OUT > 0, THEN IT IS PURCHASE:
    if np.nanmax([row["{}_{}".format(network, opposite)], 0]) > 0:

        if direction == "IN":
            return EVENTS[0]
        else:
            return EVENTS[1]
    
    #2 CHECK IF INCOME/OUTCOME, i.e. check if the Method is empty:
    if pd.isnull(row["Method"]):

        if direction == "IN":
            return EVENTS[3]
        elif direction == "OUT":
            return EVENTS[4]
        else:
            return EVENTS[5]
    
    #3 CHECK IF EXPENSE based by non-taxable events defined in config.py
    if is_item_in_list(row["Method"], dic_methods[direction]["non_taxable_events"]):
        return EVENTS[2]
    
    #4 CHECK IF PURCHASE/SALE based on taxable events defined in config.py 
    if is_item_in_list(row["Method"], dic_methods[direction]["taxable_events"]):

        if direction == "IN":
            return EVENTS[0]
        else:
            return EVENTS[1]
    
    #5 CHECK IF TRANSFER OUT:
    #NOTE this might be also defined in config.py + list might be expanded in the future
    if is_item_in_list(row["Method"], ["Transfer", "Outbound Transfer"]):

        if direction == "OUT":
            return EVENTS[4]
    
    #5 RETURN NOT DEFINED EVENT
    return EVENTS[5]


def get_price(df, network):
    """
    Get price in the transaction
    """
    print("Getting prices of purchases/sales")

    df["USD_PRICE"] = np.NaN
    duplicated_hashes = get_duplicated_txhashes(df, "Txhash")

    for index, row in df.iterrows():

        if pd.isnull(row["ContractAddress"]):
            continue
        
        row_method = row["Method"]
        row_event = row["EVENT"]

        # if EXPENSE/INCOME:
        if is_item_in_list(row_event, ["EXPENSE", "INCOME"]):

            is_claim_method = is_item_in_list(row_method, ["Claim", "Claim Tokens"])

            # if token was claimed, then set price to 0:
            if is_claim_method:
                df.loc[index, "USD_PRICE"] = 0

            # if token income, price is not known:
            elif (
                (row_event == "INCOME") & 
                (is_claim_method == False)
                ):
                 # @dev: place to put outsourced price (from oracle/api)
                df.loc[index, "USD_PRICE"] = "NOT KNOWN"

            # leave empty in other cases:
            else:
                df.loc[index, "USD_PRICE"] = ""
            continue
        
        usd_price = "NOT KNOWN"
        direction = row["TokenDirection"]

        if direction == "IN":
            opposite = "OUT"
        elif direction == "OUT":
            opposite = "IN"

        # if stable coin:
        if row["ContractAddress"] in dict_stables[network].values():
            usd_price = abs(row["Value"])

        # if sold/purchased for eth:
        elif (
            (np.nanmax([row["{}_{}".format(network, opposite)], 0]) > 0) & 
            (pd.isnull(row["{}_USD_PRICE".format(network)]) == False) &
            (str(row["{}_USD_PRICE".format(network)]) != "")
        ):
            usd_price = row["{}_{}".format(network, opposite)] * row["{}_USD_PRICE".format(network)]

        # if swapped with stable coin:
        elif row["Txhash"] in duplicated_hashes:
            token_contract_address = row["ContractAddress"]
            df_fil = df[(df["Txhash"].isin(duplicated_hashes)) & (df["Txhash"] == row["Txhash"])]

            for index2, row2 in df_fil.iterrows():
                if row2["ContractAddress"] != token_contract_address:
                    if row2["ContractAddress"] in dict_stables[network].values():
                        usd_price = abs(row2["Value"])
                        # check if event is purchase and if not assign PURCHASE to EVENT:
                        if is_item_in_list(row["EVENT"], ["PURCHASE", "SALE"]) == False:
                            if row["TokenBalanceBefore"] < row["TokenBalanceAfter"]:
                                df.loc[index, "EVENT"] = "PURCHASE"
                            elif row["TokenBalanceBefore"] > row["TokenBalanceAfter"]:
                                df.loc[index, "EVENT"] = "SALE"

        if usd_price == "NOT KNOWN":
            # @dev: place to put outsourced price (from oracle/api) 
            pass

        df.loc[index, "USD_PRICE"] = usd_price


def get_state(df, network):
    """
    Get state (cashflow) of the trade at the given transaction
    """

    print("Getting states (i.e. Cash Flow)")

    df["USD_STATE"] = np.NaN
    df.sort_values(by=["UnixTimestamp"], inplace=True)

    for index, row in df.iterrows():
        # if not a token, skip the row
        if pd.isnull(row["ContractAddress"]) == True:
            continue
        # if a stable coin, skip the row
        if is_item_in_list(row["ContractAddress"], dict_stables[network].values()):
            continue
        # if price is not know, assign MISSING DATA
        if row["USD_PRICE"] == "NOT KNOWN":
            apply_missing_data(df, index=index)
            continue
        
        unix_timestamp_now = row["UnixTimestamp"]
        contract_address = row["ContractAddress"]
        
        # Get USD_PRICE at the row:
        if (row["USD_PRICE"] == ""):
            row_price = np.nan
        else:
            row_price = float(row["USD_PRICE"])
        # if token was bought, it is has to be negative price 
        if (is_item_in_list(row["EVENT"], (["PURCHASE", "INCOME"]))) & (row_price > 0):
            row_price *= -1
        # set initial value of state (cash_flow)
        state_now = row_price
        # get only data regarding taxable events
        df_fil = df[
            (df["ContractAddress"] == contract_address) & 
            (df["UnixTimestamp"] <= unix_timestamp_now) &
            (df["EVENT"].isin(["PURCHASE", "INCOME", "SALE"]))
            ]

        if len(df_fil.index) > 0:
            # filter table in order to get state of the previous row
            if (df_fil["UnixTimestamp"].iloc[0] < unix_timestamp_now):

                nrows = len(df_fil.index)
                previous_row = df_fil.sort_index().iloc[nrows-2]
                # if data is missing, the state cannot be calculated anyway, thus assign
                #   missing data and iterate next
                if previous_row["USD_STATE"] == "MISSING DATA":
                    apply_missing_data(df, index=index)
                    continue

                # NOTE: current state (cash flow) is sum of the previous state and current price
                # get initial value of the state
                state_now = np.nansum([previous_row["USD_STATE"], row_price])
                # if previous row was SALE event and all tokens were sold, then set state to the current price
                # or if previous row was expense, set the state to the previous state
                if (previous_row.empty == False):

                    if (is_item_in_list(previous_row["EVENT"], ["SALE"])):
                        if (previous_row["TokenBalanceAfter"] == 0):
                            state_now = row_price

                    elif (is_item_in_list(row["EVENT"], ["EXPENSE"])):
                        state_now = previous_row["USD_STATE"]
        
        df.loc[index, "USD_STATE"] = state_now


def apply_missing_data(df, index, column_name="USD_STATE", argument="MISSING DATA"):
    df.loc[index, column_name] = argument


def get_status(df, network):
    """
    Get final STATUS of the trade
    Possibilities: OPENED, CLOSED, UNCLEAR or STABLES
    """
    print("Getting STATUS")
    colname = "STATUS"
    df[colname] = ""
    df.sort_values(by=["UnixTimestamp"], inplace=True)

    for index, row in df.iterrows():
        # if not a token, skip the row
        contract_address = row["ContractAddress"]
        if pd.isnull(contract_address):
            continue

        row_method = row["Method"]
        row_event = row["EVENT"]

        # STABLES
        if is_item_in_list(contract_address, dict_stables[network].values()):
            df.loc[index, colname] = "STABLES"
            continue
        
        # OPENED
        # NOTE if all conditions are met, but method is empty, it might wrongly evaluate status and user should
        # fix it manually
        if ((row["TokenBalanceBefore"] == 0) & (row["TokenBalanceAfter"] > 0) & 
            ((row_event in ["PURCHASE", "INCOME"]) | 
            (is_item_in_list(row_method, ["Claim", "Claim Tokens", "Claim Rewards"])))):
            df.loc[index, colname] = "OPENED"
            continue
        
        # CLOSED
        if (((row["TokenBalanceBefore"] > 0) & (row["TokenBalanceAfter"] == 0)) & 
            (row_event == "SALE")
            ):
            df.loc[index, colname] = "CLOSED"
            continue
        
        # Could not be assessed, thus assign "UNCLEAR"
        if (row_event in ["OUTCOME", "NOT DEFINED"]):
            df.loc[index, colname] = "UNCLEAR"
            continue



def evaluate_status(df):
    """
    Evaluate final status from function get_status. Output of this function is used for conditional formatting
    in output xlsx file
    """
    print("Evaluating status")

    colname = "A"
    df[colname] = ""
    df.sort_values(by=["UnixTimestamp"], inplace=True)

    for index, row in df.iterrows():
        # skip row if not a token
        if pd.isnull(row["TokenSymbol"]):
            continue
        # get status, token contract and timestamp
        status_row = row["STATUS"]
        # skip if STABLES
        if status_row == "STABLES":
            continue

        token_contract = row["ContractAddress"]
        unix_timestamp_row = row["UnixTimestamp"]
        
        # keep only data regarding the given token
        df_fil = df[(df["ContractAddress"] == token_contract)]
        
        # find unixtimestamp of opening trade 
        # there is no way that the trade was NOT opened
        if status_row == "OPENED":
            unix_timestamp_opened = unix_timestamp_row
        else:
            unix_timestamp_opened = df_fil.loc[
                (df_fil["UnixTimestamp"] <= unix_timestamp_row) & (df_fil["STATUS"] == "OPENED"), 
                "UnixTimestamp"
                ].max()

        # find if exist closing trade and get its timestamp; if there is more than one closing events, 
        #   get the last one;
        # if closing trade dost not exist, get timestamp of the first trade with token
        if status_row == "CLOSED":
            unix_timestamp_closed = unix_timestamp_row
        else:
            df_closed = df_fil[(df_fil["STATUS"] == "CLOSED") & (df_fil["UnixTimestamp"] >= unix_timestamp_row)]

            if len(df_closed.index) > 0:
                unix_timestamp_closed = df_closed["UnixTimestamp"].min()
            else:
                unix_timestamp_closed = df_fil["UnixTimestamp"].max()
        
        # get data frame containg data of the given trade
        df_fil = df_fil[
            (df_fil["UnixTimestamp"] >= unix_timestamp_opened) & 
            (df_fil["UnixTimestamp"] <= unix_timestamp_closed)
            ]
        
        # get array of columns to analyze it further
        array_fil = np.array(df_fil[["EVENT", "USD_PRICE", "USD_STATE", "STATUS"]])
        
        # set status to be open (O)
        status = "O"

        if "CLOSED" in array_fil:
            status = "C"

        # change status if some missing data etc.
        for item in ["NOT KNOWN", "MISSING DATA", "UNCLEAR"]:
            if item in array_fil:
                status = "U"
        
        # assign status to the given row
        df.loc[index, colname] = status
