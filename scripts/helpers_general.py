import pandas as pd

from config import dict_links


def csv_to_df(file_name, delete_columns=None):
    dt = pd.read_csv(file_name, delimiter=",", header=0, index_col=False, decimal=".", thousands=",")
    if delete_columns:
        dt.drop(columns=delete_columns, inplace=True)
    return dt


def get_duplicated_txhashes(df, col_name):
    """
    Return list of transaction hashes in the given dataframe from the given column name
    """
    seen = set()
    dupes = [x for x in df[col_name] if x in seen or seen.add(x)]
    return dupes


def move_columns_at_front(df, columns):
    """
    Move columns in df at the front positions
    """
    index = 0
    for col in columns:
        col_to_move = df.pop(col)
        df.insert(index, col, col_to_move)
        index += 1


def correct_usd_fees(df, network):
    for index, row in df.iterrows():
        if network == "ETH":
            network_capital = network.capitalize()
            df.loc[index, "TxnFee(USD)"] = row["TxnFee({})".format(network)] * row["Historical $Price/{}".format(network_capital)]
        else:
            df.loc[index, "TxnFee(USD)"] = row["TxnFee({})".format(network)] * row["Historical $Price/{}".format(network)]


def add_hyperlinks_to_column(dt, col_name, network):
    dt[col_name] = ""
    for index, row in dt.iterrows():
        dt.loc[index, col_name] = "{}{}".format(dict_links[network], row["Txhash"])


def is_item_in_list(item_to_check, list_to_explore):
    # if item to check is empty return FALSE
    if pd.isnull(item_to_check):
        return False
    # check if item in the list
    for item in list_to_explore:
        # print("Checking if '{}' in '{}'".format(item.lower(), item_to_check.lower()))
        if item.lower() in item_to_check.lower():
            if item.lower() != '':
                return True
    # if not return False
    return False


def main():
    pass


if __name__ == "__main__":
    main()