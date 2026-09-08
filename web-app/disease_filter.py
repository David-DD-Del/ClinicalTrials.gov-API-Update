import re

cardio_exclusion_set = {
    # Hematologic & Blood Protein
    "Hemostatic Disorders", "Blood Protein Disorders", "Cryoglobulinemia",
    "Disseminated Intravascular Coagulation", "Purpura",
    "Purpura, Thrombocytopenic", "Purpura, Hyperglobulinemic",
    "Shwartzman Phenomenon", "Angioedemas, Hereditary", "Hemorrhoids",

    # Oncologic & Neoplastic
    "Multiple Myeloma", "Leukemia, Plasma Cell", "Plasmacytoma",
    "Waldenstrom Macroglobulinemia", "Hemangioma", "Hemangioma, Cavernous",
    "Neoplastic Syndromes, Hereditary",

    # Genetic, Metabolic, & Storage
    "Fabry Disease", "Fabry Disease, Cardiac Variant", "Amyloidosis",
    "Gaucher Disease", "Tangier Disease", "Diabetic Angiopathies",
    "Diabetic Retinopathy", "Diabetic Foot", "Scurvy",

    # Connective-Tissue & Autoimmune
    "Marfan Syndrome", "Ehlers-Danlos Syndrome", "Pseudoxanthoma Elasticum",
    "Sarcoidosis", "Lupus Erythematosus, Systemic",
    "Telangiectasia, Hereditary Hemorrhagic",

    # Infectious
    "Syphilis, Cardiovascular", "Tuberculosis, Cardiovascular"
}
# Build the regex pattern (e.g., "Purpura|Amyloidosis|Scurvy")
exclusion_pattern = '|'.join(re.escape(term) for term in cardio_exclusion_set)

def cardio_filter(dataframe):
    """Broad filter on cardiovascular diseases from exclusion pattern"""
    dataframe = dataframe[
        ~dataframe['mesh_terms'].str.contains(exclusion_pattern, case=False, na=False)
    ]
    return dataframe


cardio_crossover_ex = ['Diabetes Mellitus, Type 2', 'Renal Insufficiency, Chronic', 'Obesity',
                       'Diabetes Mellitus', 'Overweight', 'COVID-19']
auto_crossover_ex = ['Diabetes Mellitus, Type 1', 'Diabetes Mellitus, Type 2', 'Diabetes Mellitus',
                     'Kidney Diseases', 'Renal Insufficiency, Chronic']
kidn_cross_ex = ['Diabetes Mellitus, Type 1', 'Diabetes Mellitus, Type 2', 'Diabetes Mellitus',
                 'Autoimmune Diseases', 'Hypertension', 'Obesity', 'Heart Failure', 'COVID-19',
                 'Overweight']
liv_cross_ex = ['Diabetes Mellitus, Type 1', 'Diabetes Mellitus, Type 2', 'Diabetes Mellitus',
                 'Autoimmune Diseases', 'Obesity', 'Overweight', 'Melanoma', 'Colorectal Neoplasms',
               'Stomach Neoplasms', 'Ovarian Neoplasms', 'Breast Neoplasms', 'Lung Neoplasms',
               'Pancreatic Neoplasms']
obes_cros_ex = ['Diabetes Mellitus, Type 1', 'Diabetes Mellitus, Type 2', 'Diabetes Mellitus',
                'Non-alcoholic Fatty Liver Disease', 'Renal Insufficiency, Chronic']
dia_cros_ex = ['Obesity', 'Overweight', 'Renal Insufficiency, Chronic', 'Hypertension',
               'Kidney Diseases', 'Retinal Diseases']

def narrow_filter(master_df):
    """Narrow filter: filters out MeSH terms that are in the wrong category"""
    # Identify the specific rows that meet BOTH conditions
    rows_to_drop_c = (master_df['seed_term'] == 'cardiovascular diseases') & (master_df['mesh_terms'].isin(cardio_crossover_ex))
    master_df = master_df[~rows_to_drop_c]
    rows_to_drop_a = (master_df['seed_term'] == 'autoimmune diseases') & (master_df['mesh_terms'].isin(auto_crossover_ex))
    master_df = master_df[~rows_to_drop_a]
    rows_to_drop_k = (master_df['seed_term'] == 'kidney diseases') & (master_df['mesh_terms'].isin(kidn_cross_ex))
    master_df = master_df[~rows_to_drop_k]
    rows_to_drop_l = (master_df['seed_term'] == 'liver diseases') & (master_df['mesh_terms'].isin(liv_cross_ex))
    master_df = master_df[~rows_to_drop_l]
    rows_to_drop_o = (master_df['seed_term'] == 'obesity') & (master_df['mesh_terms'].isin(obes_cros_ex))
    master_df = master_df[~rows_to_drop_o]
    rows_to_drop_d = (master_df['seed_term'] == 'diabetes mellitus') & (master_df['mesh_terms'].isin(dia_cros_ex))
    master_df = master_df[~rows_to_drop_d]

    return master_df