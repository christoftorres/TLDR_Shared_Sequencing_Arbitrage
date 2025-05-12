#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import requests
import pandas as pd

# INPUT
STARTING_DATE  = "2024-11-01"
ENDING_DATE    = "2024-11-01"
CHAINS         = ["arbitrum", "optimism", "base"]
MAX_SWAP_COUNT = 5

# OUTPUT
OUTPUT_FOLDER  = "fees"

class colors:
    INFO = '\033[94m'
    OK = '\033[92m'
    FAIL = '\033[91m'
    END = '\033[0m'


def main():
    if len(sys.argv) < 2:
        print(colors.FAIL+"Error: Please provide an Allium API key to download transaction fees: 'python3 "+sys.argv[0]+" <ALLIUM_API_KEY>'"+colors.END)
        sys.exit(-1)

    allium_api_key = sys.argv[1]

    for chain in CHAINS:
        for swap_count in range(1, MAX_SWAP_COUNT + 1):

            if not os.path.exists(OUTPUT_FOLDER+"/"+chain+"/"):
                os.makedirs(OUTPUT_FOLDER+"/"+chain+"/")
        
            period_range = pd.period_range(start=STARTING_DATE, end=ENDING_DATE, freq="D")
            dates = tuple([(period.year, period.month, period.day) for period in period_range])
            
            for date in dates:
                start_date = str(date[0])+"-"+"{:02d}".format(date[1])+"-"+"{:02d}".format(date[2])+"T00:00:00"
                end_date = str(date[0])+"-"+"{:02d}".format(date[1])+"-"+"{:02d}".format(date[2])+"T23:59:59"

                if not os.path.exists(OUTPUT_FOLDER+"/"+chain+"/"+chain+"_"+str(swap_count)+"_transaction_fees_"+str(date[0])+"_"+"{:02d}".format(date[1])+"_"+"{:02d}".format(date[2])+".json"):

                    print("Downloading transaction fees on "+chain.capitalize()+" for swap count "+str(swap_count)+" from", start_date, "to", end_date)
                    download_start = time.time()

                    # Create a query run
                    response = requests.post(
                        "https://api.allium.so/api/v1/explorer/queries/Fsgqyna1VrcP3LLYKp5b/run-async",
                        json={"parameters": {"chain": chain, "swap_count": str(swap_count), "block_timestamp_start": start_date, "block_timestamp_end": end_date}, "run_config": {"limit": 250000}},
                        headers={"X-API-Key": allium_api_key}
                    )
                    query_run_id = response.json()["run_id"]
                    
                    # Poll for query run status
                    while True:
                        response = requests.get(
                            "https://api.allium.so/api/v1/explorer/query-runs/"+query_run_id,
                            headers={"X-API-Key": allium_api_key}
                        )
                        if not response.json()["status"] in ["queued", "running"]:
                            break
                        time.sleep(2)

                    # Fetch results
                    response = requests.post(
                        "https://api.allium.so/api/v1/explorer/query-runs/"+query_run_id+"/results",
                        headers={
                            "X-API-Key": allium_api_key,
                            "Content-Type": "application/json"
                        },
                        json={"config": {}}
                    )

                    download_stop = time.time()                
                    print("Download took:", download_stop - download_start, "second(s).")

                    fees = list()
                    for fee in response.json()["data"]:
                        fees.append(fee)

                    with open(OUTPUT_FOLDER+"/"+chain+"/"+chain+"_"+str(swap_count)+"_transaction_fees_"+str(date[0])+"_"+"{:02d}".format(date[1])+"_"+"{:02d}".format(date[2])+".json", "w") as f:
                        json.dump(fees, f, indent=4)
                    print("Saved", len(fees), "transaction fee instances.")


if __name__ == "__main__":
    main()
