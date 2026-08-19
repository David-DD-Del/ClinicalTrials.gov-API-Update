import pandas as pd
import api_call
import disease_filter
import sponsor_norm
import mesh_mapping
import scoring

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

if __name__ == "__main__":
    # Runs our pipeline.
    dataf = {}
    for term in seed_terms:
        dfname = "df_" + term[0:3]
        dataf[dfname] = api_call.run_pipeline(term)

    # Filter out excluded Cardiovascular Diseases
    dataf['df_car'] = disease_filter.cardio_filter(dataf['df_car'])

    # Concatenate all dataframes in the dictionary into one single dataframe
    master_df = pd.concat(dataf.values(), ignore_index=True)

    # Filter out diseases that are not wanted
    master_df = disease_filter.narrow_filter(master_df)

    # Filter out devices
    master_df = master_df[~master_df['intervention_type'].str.contains('device', case=False, na=False)]

    # Normalize sponsor names
    master_df = sponsor_norm.sponsor_norm(master_df)

    # Check the shape of the new combined dataframe
    print(f"\nRows for all diseases after filtering {master_df.shape[0]}.\n")

    # Filter for all rows that share a duplicate nct_id
    duplicates_df = master_df[master_df['nct_id'].duplicated(keep=False)]

    # Group by your seed term column and count the rows
    duplicate_counts = duplicates_df.groupby('seed_term').size().reset_index(name='duplicate_count')

    # Sort from highest amount of duplicates to lowest
    duplicate_counts = duplicate_counts.sort_values(by='duplicate_count', ascending=False)

    print("Current duplicate trials per term")
    print(duplicate_counts)

    # create updated mesh_mapping CSV file
    mesh_mapping.mesh_mapping(master_df)

    # create scoring CSV and add global counts for early active trials to master df
    master_df = scoring.scoring_system(master_df)

    # create updated  all diseases csv file
    master_df.to_csv('all_diseases.csv', index=False)
    print("Created CSV file containing all trials with filename: all_diseases.csv")