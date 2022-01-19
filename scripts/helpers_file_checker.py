import os
import shutil

from config import networks_list
from helpers_general import csv_to_df


dict_file_types = {
    'TOKENS': [
        'TokenName', 'TokenSymbol',
        ],
    'INTERNAL': [
        'ParentTxFrom', 'ParentTxTo', 'ParentTxETH_Value', 'Type',
        ],
    'TXS': [
        'Method',
    ],
    }

# columns to be checked in order to get owner address (suppose that the owner is the most frequent address) 
# in each type of export 
dict_columns_to_check = {
    "TOKENS": ["From", "To"],
    "INTERNAL": ["ParentTxFrom", "ParentTxTo", "From", "TxTo"],
    "TXS": ["From", "To"],
}


def get_all_csv_files(dir_path, suffix=".csv"):
    """
    Get all *.csv (if not specifed else) files in the folder

    Args:
        dir_path (string): path to the dictionary with the files
        suffix (string): suffix to be used in filtering of files   
    Returns:
        (list): all files in the folder with the given suffix
    """

    files = os.listdir(dir_path)
    return [file for file in files if file.endswith(suffix)]


def find_type_of_export(file_path):

    dt = csv_to_df("./input/{}".format(file_path))

    for file_type, file_columns in dict_file_types.items():
        # file_type = key in dict_file_types, i.e. a file type
        if set(file_columns).issubset(dt.columns):
            # convert defined columns in to a numpy array
            arr_addresses = dt[dict_columns_to_check[file_type]].to_numpy()
            # from numpy array above convert to a list
            ls_addresses = [x for i in arr_addresses for x in i]
            # get the most frequent address in the ls_addresses (=owner address)
            address = max(ls_addresses, key=ls_addresses.count)
            return (file_path, file_type, address)


def check_for_network(file_path, network_list):
    df = csv_to_df("./input/{}".format(file_path))
    columns = ";".join(df.columns)
    for network in network_list:
        # NOTE all EVM chains has capital ticker in all columns, but in the case of ETH some ticker is capital some not,
        #   thus I needed define network_adjusted variable to handle this
        network_adjusted = network
        if network == "ETH":
            network_adjusted = network.capitalize()
        if "/{}".format(network_adjusted) in columns:
            return network


def file_checker(dir_path="./input"):
    csv_files = get_all_csv_files(dir_path)
    output_ls = []
    for file in csv_files:
        output_ls.append([find_type_of_export(file), check_for_network(file, networks_list)])
    return output_ls


def validate_input_files(files_info):
    print("Starting validation process of input files")
    # Assign
    addresses = []
    networks = []
    validated = False
    # Extract data
    for (_, _, address), network in files_info:
        print("... network: {}, address: {}".format(network, address))
        if network:
            networks.append(network)
        if address:
            addresses.append(address)
    # validation
    only_one_network = (len(set(networks)) == 1)
    only_one_address = (len(set(addresses)) == 1)
    all_files_contains_address = (len(addresses) == 3)
    if all_files_contains_address & only_one_address & only_one_network:
        validated = True
    return [validated, set(networks), set(addresses), len(addresses)]


def move_csv_files_from_src_to_dest(dir_src=".\\input", dir_dest=".\\temp"):
    all_files = get_all_csv_files(dir_src)
    for file in all_files:
        if file:
            print(os.path.join(dir_src, file))
            if os.path.exists(os.path.join(dir_dest, file)):
                os.remove(os.path.join(dir_src, file))
            else:
                shutil.move(os.path.join(dir_src, file), dir_dest)


def main():
    pass


if __name__ == "__main__":
    main()

