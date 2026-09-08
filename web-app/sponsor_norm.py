import pandas as pd

df_comps = pd.read_csv('data/industry_norm_final.csv')

def sponsor_norm(master_df):
    """Normalize sponsor names using df_comps, if sponsor is not part of
        df_comps fill with raw sponsor name from master_df"""
    # Create a mapping series by setting the index to the shared key and isolating the target column
    right_mapping = df_comps.set_index('raw_sponsor_name')['dashboard_sponsor_name']
    parent_mapping = df_comps.set_index('raw_sponsor_name')['parent_rollup_name_if_approved']

    # Map those values directly to a new column in the left dataframe
    master_df['sponsor_norm'] = master_df['sponsor'].str.strip().map(right_mapping)
    master_df['parent_sponsor'] = master_df['sponsor'].str.strip().map(parent_mapping)

    # Fills missing values in 'main_column' with values from 'backup_column'
    master_df['sponsor_norm'] = master_df['sponsor_norm'].fillna(master_df['sponsor'])
    master_df['parent_sponsor'] = master_df['parent_sponsor'].fillna(master_df['sponsor_norm'])

    return master_df