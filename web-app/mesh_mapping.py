import pandas as pd
import browser_download

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
    browser_download.download_csv(mesh_mapping, "mesh_mapping.csv")
    print("Triggered browser download for: mesh_mapping.csv\n")