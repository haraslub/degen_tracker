import datetime
from numpy import add
import pandas as pd

from helpers_file_checker import (
    file_checker, move_csv_files_from_src_to_dest, validate_input_files
    )
from helpers_general import (
    csv_to_df, move_columns_at_front, add_hyperlinks_to_column, correct_usd_fees
)
from helpers_data_process import (
    get_token_direction, get_token_balance, extract_usd_price_of_eth_from_column, get_eth_io_and_balance,
    get_event, get_price, get_state, get_status, evaluate_status
)
from helpers_excel import (
    xlsx_export, xlsx_export_data_to_sheet, xlsx_update, xlsx_create_overview, xlsx_open
)
from config import (
    delete_columns_tokens, delete_columns_txs, 
    _columns_to_be_moved, _columns_to_be_merged, _columns_final_order,
    _dict_headers_rename, _dict_colums_float,
    MERGE_AND_EXPORT, DEV_MODE, 
    adjust_list, adjust_dict
)

export_file_tokens = ""
export_file_txs = ""
export_file_internal = ""

address = ""
network = "ETH"


def main():
    # Get info about the input files 
    input_files_info = file_checker()
    # Validate input files
    validation_success, network, address, number_of_addresses = validate_input_files(input_files_info)
    
    if validation_success:
        
        network = "".join(network)
        address = "".join(address)

        # create input variables from input files info
        for (file_path, file_type, _), _ in input_files_info:
            globals()["export_file_{}".format(file_type.lower())] = "./input/{}".format(file_path)
        # TODO: add check that address is same in all three tuples in input_files_info:
        # address = input_files_info[0][2]
        # create output file name
        output_xlsx = "./output/{}_{}_{}.xlsx".format(address, network, datetime.datetime.now().strftime("%Y-%m-%d"))

        # adjust data from config to the actual network
        columns_to_be_moved = adjust_list(_columns_to_be_moved, network)
        columns_to_be_merged = adjust_list(_columns_to_be_merged, network)
        columns_final_order = adjust_list(_columns_final_order, network)
        dict_headers_rename = adjust_dict(_dict_headers_rename, network)
        columns_fo_float = adjust_list(_dict_colums_float[network], network)
        
        # proces erc20 tokens transactions
        df_tokens = csv_to_df(export_file_tokens, delete_columns_tokens)
        df_tokens = get_token_direction(df_tokens, address)
        df_tokens = get_token_balance(df_tokens)
        
        # proces transactions
        df_txs = csv_to_df(export_file_txs, delete_columns_txs)
        df_txs[columns_fo_float] = df_txs.loc[:, columns_fo_float].astype(float)
        correct_usd_fees(df_txs, network)
        df_txs = get_token_direction(df_txs, address)
        
        # proces internal transations
        df_internal = csv_to_df(export_file_internal, delete_columns_txs)
        
        # merge transactions with internal transactions

        # NOTE all EVM chains has capital ticker in all columns, but in the case of ETH some ticker is capital some not,
        #   thus I needed define network_adjusted variable to handle it
        network_adjusted = network
        if network == "ETH":
            network_adjusted = network.capitalize()

        df_txs_int = pd.merge(
            df_txs, df_internal, how="outer", 
            on=["Txhash", "UnixTimestamp", "Historical $Price/{}".format(network_adjusted)]
            )
        get_eth_io_and_balance(df_txs_int, network)
        extract_usd_price_of_eth_from_column(df_txs_int, network)
        move_columns_at_front(df_txs_int, columns_to_be_moved)

        # merge tokens and merged file of txs and internal txs
        dt_merged = pd.merge(df_tokens, df_txs_int[columns_to_be_merged], how="outer", on=["Txhash", "UnixTimestamp"])
        dt_full_merged = pd.merge(df_tokens, df_txs_int, how="outer", on=["Txhash", "UnixTimestamp"])

        # data manipulation and evaluation
        dt_merged.sort_values(by=["UnixTimestamp"], inplace=True)
        get_event(dt_merged, network)
        get_price(dt_merged, network)
        get_state(dt_merged, network)
        get_status(dt_merged, network)
        evaluate_status(dt_merged)
        move_columns_at_front(dt_merged, columns_final_order)
        add_hyperlinks_to_column(dt_merged, "HYPERLINK", network)
        
        if MERGE_AND_EXPORT:
            print("Exporting results")
            # export to xlsx output file and final adjustments in the output file
            # 1) rename columns in the final data frame
            dt_merged.rename(columns=dict_headers_rename, inplace=True)
            # 2) export final data frame to the xlsx file
            xlsx_export(output_xlsx, dt_merged, network)
            # 3) export all data to the xlsx file (hidden sheet in default)
            xlsx_export_data_to_sheet(output_xlsx, dt_full_merged)
            # 4) apply conditional formating, create filter, wrap header etc.
            xlsx_update(output_xlsx, "full_data", list(set(dt_merged["Token Symbol"])), dt_merged)
            # 5) create overview list with the final calculations
            xlsx_create_overview(output_xlsx)
            # 6) open the output excel file
            xlsx_open(output_xlsx)
            # move files from input folder to temp folder
            if DEV_MODE == False:
                move_csv_files_from_src_to_dest()

    else:
        print("Validation test did not go trough, see details below:")
        if len(network) != 1:
            print("... expceted only one network to be found in input files. Networks found:")
            for n in network:
                print(n)
        if len(address) != 1:
            print("... expceted only one address to be found in input files. Addresses found:")
            for a in address:
                print(a)
        if number_of_addresses != 3:
            print("... expected 3 addresses to be found. Instead get: {} addresses".format(number_of_addresses))
    

if __name__ == "__main__":
    main()