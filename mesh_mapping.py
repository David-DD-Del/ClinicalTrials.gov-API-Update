import pandas as pd
import data_utils

def mesh_mapping(master_df):
    # Isolate the ID and the mesh_terms
    mesh_df = master_df[['nct_id', 'mesh_terms']].copy()

    # Fill blank mesh_terms with a placeholder so the trial is preserved
    mesh_df['mesh_terms'] = mesh_df['mesh_terms'].fillna('Unassigned')

    # Split the string by the pipe delimiter into a list
    mesh_df['Indication'] = mesh_df['mesh_terms'].str.split('|')

    # Explode the lists into individual rows
    mesh_mapping = mesh_df.explode('Indication')[['nct_id', 'Indication']]

    # Strip any accidental whitespace
    mesh_mapping['Indication'] = mesh_mapping['Indication'].str.strip()

    # Export as a separate mapping table for Tableau
    data_utils.save_csv(mesh_mapping, 'mesh_mapping.csv')

    print('Mesh mapping CSV created with filename: mesh_mapping.csv', flush=True)