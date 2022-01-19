# DEGEN TRACKER

## Read first

This is my first Python open source project and it is very likely full of bad practices and security issues. You **should not** use this code without proper testing as I have not done that (especially for different networks than Ethereum). Although if you are interested in learning a bit about how to analyze your degen accounts you may find it engaging. Use it **at your own risk**. Any ideas, suggestions of how to improve my code are very welcome.

## Overview

Motivation to create Degen Tracker was to facilitate processing transactions over different networks. Unfortunately, I could not find any app which would be reliable enough and which would provide me with the good user experience and simultaneously have good access to data to be able to check them. As used to working with MS Excel, I decided to process transaction data from etherscan (or other networks' scans) and export them to the \*.xlsx file (output file) in which then I could work easily. The process is not fully automated, there are already known **bugs**. Thus, **user is always supposed to revise the whole report!**.

## Requirements

It is meant to be used by users having at least basic technical knowledge of Python and MS Excel. The project will not work unless you meet the following conditions:

- user has downloaded all necessary input data in csv format, i.e.: transactions (1), internal transactions (2) and Erc20 Token Transactions from the given etherscan-ish (depending on network) website containing every single transaction since the very beginning;
- user has placed those files into the input data folder;
- Python, MS Excel installed (it was developed on WIN 10, Python 3.9.7);

You should also:

- check all the address of stable coins (config_stables.py) and add others if needed;

## Assumptions

If you are about to use it, you should consider following assumptions:

- All **price feeds** used origin from the downloaded CSV files, i.e. from the ethescan-ish type of files and might be different to reality.
- Only **token swaps** are subjects of the data processing. Other operations, i.e. liquidity providing, will appear in the output file as well, but their **the output does not correspond to reality.** Hence, a user should process them separately.
- **Stablecoins** if a token is swapped with USD pegged stablecoin defined in config_stables.py, the token is priced by stable coin amount used in the token swap. Deviations to real USD value are not considered.
- **Taxable/non-taxable events** are defined in config.py, but they were not extracted from any legislation. Instead a common sense was applied. Thus,a user should check and adjust it before usage if he/she plans to use it for their tax report.
- The project is not fully **automatic**, if data is missing, user has to fill them in the output excel in the proper way (see Manual section below).
- **Fees** are not considered as part of the price paid during operations with tokens. On the contrary, they are calculated separately and can be seen in the sheet Overview.

## TODO

Things I should have done but haven’t as I mentioned this project was a learning opportunity for me. Below find a list of improvements that could be done to this project.

- The project does not take into account other transactions made, i.e. ERC721 Token Transactions, ERC1155 Token Transaction etc., thus the total fee is not calculated properly.
- If the price of token is not known, there could be used some external source of data price (API).
- If user buys and sells the same token multiple times and the Token Balance never reaches 0 in the reporting period, it will not be included in the final calculations (see Output section below), hence user would need to handle it manually (or at least have once zero token balance) if he/she wants to have it included.
- If a user doesn’t use all the three kind of input data, process might fail (not tested), thus it should be handled as well.
- There are several already know bugs/inconsistencies which need user's manual interaction (see Example part below). This means that there might be others which have not been discovered yet.
- Also no thorough testing has been performed, especially for other chains.
- If a user wants to process transactions from several addresses, he/she needs to put the input data in the input folder manually after each iteration. It could be automated as well.
- Processing of liquidity provision might be a subject of further development.
- There could be a function to take it into account if addresses' transaction has been already processed in the past (the output file exists), and process only new transactions.

## Output

The output file name is in form your-address_network-ticker_YYYY-MM-DD.xlsx. The output file is file with two sheets: 1) full data and 2) overview.

### Sheet full_data

In this section, you can find description of the columns in the output file.

**full_data sheet**

- Token Symbol = the ticker of the given token;
- A = final assessment regarded to token operations used for the final calculation and conditional formatting in the output file. Assessments:
  - C = completed; the result operation is considered in the final calculation (see the sheet overview);
  - O = open; the result of operation is not considered in the final calculation as the trade has not been closed yet;
  - U = uncompleted; the result of operation is not considered in the final calculation although the trade has already been closed but there is missing data. Data needs to be revisited, filled in, and then state can be changed to "C" value in order to include changes in the final calculation.
- Token Direction = direction of the token - two possible directions:
  - IN = tokens were sent to the wallet,
  - OUT = tokens were sent out of the wallet).
- Unix Timestamp = Unix Timestamp of the transaction.
- Value = the amount of tokens included in the transaction; if Token Direction is OUT, the value is negative.
- Token Balance Before = the token balance before the execution of the transaction.
- Token Balance After = the token balance after the execution of the transaction.
- ETH IN = value is non zero if ETH (or other L1 coins depending on the given network) was sent to the account in the transaction.
- ETH OUT = value is non zero if ETH (or other L1 coins depending on the given network) was sent from the account in the transaction.
- ETH USD = the price of ETH (or other L1 coins depending on the given network) in the time of the transaction.
- Method = the name of the method (type of token operation) used in the transaction.
- Event = an Event assigned based on the type of transaction; all events are defined in config.py.
- USD price = price of the purchase/sale of transaction if known.
- USD state = the cashflow of the trade of the given token at the given time, i.e. each token is evaluated separately.
- Status = status of the operation. Can be:
  - OPEN = the trade has not been closed yet;
  - UNCLEAR = there is missing data, the transaction has to be revised by user;
  - CLOSED = the trade has been closed, i.e. value in Token Balance After column reached 0;
  - STABLES = the trade relates to stables (and it is not considered for further calculations).
- Hyperlink = hyperlink to the transaction.

**overview sheet**

- Profit brutto: sum of all transaction with CLOSED value in the Status column and with C value in the S column in the given time (see Date from, Date to)
- Fees: sum of all transaction fees in the given time (see Date from, Date to)
- Profit netto: Profit brutto - Fees
- Date from: Date of the beginning of the taxable period (including)
- Date to: Date of the the end of the taxable period (excluding)

## Manual / Handling missing data

**DISCLAIMER:** all data (i.e. token names, price etc.) in the section were made up for learning purposes.

### General usage

1. Clone the project to your computer.
2. Download all three input files of address to be processed (see image below) to the input folder.
3. In root folder of the project run command `python scripts/data_process.py` in your source-code editor.
4. Once the process is successfully finished, the output file will open.
5. Finally, all input files are moved to the temp folder.

![Download these files](/img/download_input_data.PNG)

### Working with the output file

A) PRICE IS NOT KNOWN -> MISSING DATA -> ASSESSMENT: UNCOMPLETED

In the picture below, you can see four transactions of EXMPL1 token. The second transaction is missing USD price, thus all operations with tokens are assessed as UNCLEAR (see value "U" in the column "S"). In order to fix it, user needs to:

- fill the USD price (might be zero or else) for second transaction,
- manually recalculate cashflow in the column USD state,
- change the value "U" to "C" to all transactions.
  Once this is done (see the pictures below), the whole operations regarded to the token will be included in the final calculation (sheet overview).

![EXMPL1: Before manual revision](/img/EXMPL1_01.PNG)

![EXMPL1: After manual revision](/img/EXMPL1_02.PNG)

B) OPENED TRADE -> ASSESSMENT: OPEN

The example of open trade can be seen in the picture below. The trade consists of three operations so far. You can see "NOT DEFINED" (and MISSING DATA in the column USD price) event is in the second transaction. In this case it is not obvious if the tEXMPL2 (Tokemak t Asset) will be traded, transferred, or reclaimed in the future. This trade is not included in the final calculation (sheet overview).

![EXMPL2: Open trade](/img/EXMPL2_01.PNG)

C) ALL DATA AVAILABLE -> ASSESSMENT UNCOMPLETED AND OPEN

In the pictures below you can see two assessments. The first transaction is assessed as OPEN, the second and the third transactions are assessed as UNCOMPLETED. What happened here is that the project with token EXMPL3 was rugged, thus it distributed a new coin with the same ticker. Hence, the following procedure can be used:

- the USD price of the first transaction can be applied to the second transaction,
- the USD state (cash flow) can be then calculated for transaction 2 and 3,
- as the Status of the third transaction equals to CLOSED, the values in "A" column can be changed to C (= completed).
  After this procedure was applied, the trade will be included in the final calculation (sheet overview).

![EXMPL3: Before manual revision](/img/EXMPL3_01.PNG)

![EXMPL3: After manual revision](/img/EXMPL3_02.PNG)

D) ALL DATA AVAILABLE -> ASSESSMENT: COMPLETED

This trade represents an aidrop (transaction one) and its sale to DAI token. All data are available, thus trade can be assessed as COMPLETED and no further actions are required.

![EXMPL2: Closed trade](/img/EXMPL4_01.PNG)

E) OVERVIEW SHEET

The final calculation can be seen in the sheet "overview". In the pictures below, you can see overview list before all adjustments were made in the steps A-D and after that. I believe that formulas used in the \*.xlsx file are self-explanatory.

![Final calculation before adjustments](/img/FINAL_BEFORE.PNG)

![Final calculation after adjustments](/img/FINAL_AFTER.PNG)

## Donation

You can donate me:

- Ethereum (or BSC, Fantom, Avalanche, Polygon, zkSync, Arbitrum etc.) to: 0xc264EF4c715B9FdC44487253095C2643BD06F11b
