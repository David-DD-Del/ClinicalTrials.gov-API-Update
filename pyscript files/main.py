import asyncio
import pandas as pd
import js
import api_call
import disease_filter
import sponsor_norm
import mesh_mapping
import scoring
import browser_download
from pyodide.ffi import jsnull

# search terms
seed_terms = [
    "cardiovascular diseases",
    "kidney diseases",
    "liver diseases",
    "diabetes mellitus",
    "obesity",
    "autoimmune diseases",
    "rare disease"
]

async def main():

    while True:
        # 2. Swap standard input() for js.prompt()
        update = js.prompt("Do you want to update all CSV files or just the main one?\nPlease type 'all' or 'one': ")
        
        # 3. Handle the case where a user clicks "Cancel" on the popup
        if update is None:
            print("Operation cancelled by user.\n Refresh this page to rerun the program.")
            return # Safely exit the pipeline
            
        update = update.lower().strip()
        
        if update == "all" or update == "one":
            break
        else:
            print("I didn't get that, please try again.\n")
            
    dataf = {}
    for term in seed_terms:
        dfname = "df_" + term[0:3]
        # Await the pipeline run
        dataf[dfname] = await api_call.run_pipeline(term)

    dataf['df_car'] = disease_filter.cardio_filter(dataf['df_car'])
    master_df = pd.concat(dataf.values(), ignore_index=True)
    master_df = disease_filter.narrow_filter(master_df)

    master_df = master_df[~master_df['intervention_type'].str.contains('device', case=False, na=False)]
    master_df = sponsor_norm.sponsor_norm(master_df)

    print(f"\nRows for all diseases after filtering {master_df.shape[0]}.\n")

    duplicates_df = master_df[master_df['nct_id'].duplicated(keep=False)]
    duplicate_counts = duplicates_df.groupby('seed_term').size().reset_index(name='duplicate_count')
    duplicate_counts = duplicate_counts.sort_values(by='duplicate_count', ascending=False)

    if update == 'all':
        print("Current duplicate trials per term")
        print(duplicate_counts)
        print()
    
        mesh_mapping.mesh_mapping(master_df)
    
        # Await the scoring system
        master_df = await scoring.scoring_system(master_df)
    
        browser_download.download_csv(master_df, "all_diseases.csv")
        print("Triggered browser download for: all_diseases.csv\n")
        print("All requested CSV files have been downloaded.")
    elif update == 'one':
        # create updated  all diseases csv file
        browser_download.download_csv(master_df, "all_diseases.csv")
        print("Triggered browser download for: all_diseases.csv\n")
        print("All requested CSV files have been downloaded.")
    else:
        print("Something went wrong. Please rerun the program.")

# Trigger the event loop for PyScript
asyncio.ensure_future(main())
