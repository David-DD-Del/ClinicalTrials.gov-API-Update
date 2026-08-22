# ClinicalTrials.gov-API-Update
[How to Use with or without Python Installed](#how-to-use)  
[Excel Warning](#csv-and-excel-warning)  
[How the Trials are Filtered](#how-the-data-is-filtered)  
[CSV Files Breakdown](#csv-files-breakdown)  

## How to Use
### Python Installed
1. Download and unzip files to folder of choice.  
2. Open your terminal in this folder or navigate to this folder from terminal.  
3. Run `pip install -r requirements.txt` to install required packages.
4. Run `python3 main.py`.  
	(*Note*: `python3` may be `python` depending on how Python is installed on your OS.)  
5. The program will ask if you want all the CSV files for Tableau to be updated or just the main CSV containing all the clinical trials.  
6. The program will proceed to update and overwrite the CSV files in the current folder.
### Python Not Installed
1. If Python is not installed or you don't want to install Python, you can run the program through your browser of choice.  
2. You can either [run the program through PyScript here](https://pyscript.com/@jhvzxc/clinical-trials-api-update/) where I already set up an account and public project or create your own [PyScript account](https://pyscript.net/), start a new project and place all files from `pyscript files` folder into the files section.  
3. Once setup ensure `main.py` is selected from the files section and click `Run` button in the upper middle section.  
4. A browser popup will ask if you want all the CSV files for Tableau or just the main CSV containing all the clinical trials.  
5. The program will proceed to create the CSV files and download them through your browser.  

I'm unsure if PyScript works for all browsers; Google Chrome is recommended.
## CSV and Excel Warning
If you want to view these CSV files in Excel, don't open them with double click if Excel is your default program for CSV files. Excel will misinterpret that commas that live inside the free-text sections.

Instead open Excel first, then load the CSV file from the data tab and load it based on the entire dataset.

You may have to hit the transform button also if Excel misinterprets the headers and adds Column1, Column2, etc.
## How the Data is Filtered
### 1. API-Level Query Filters (`api_call.py`)

When querying the ClinicalTrials.gov API endpoint for disease terms, parameters filter trials before retrieval:

- **Indication Seed Terms**: Queries trials matched against specific seed terms (`"cardiovascular diseases"`, `"kidney diseases"`, `"liver diseases"`, `"diabetes mellitus"`, `"obesity"`, `"autoimmune diseases"`, `"rare disease"`) via `"query.cond"`.
    
- **Start Date**: Restricted to trials starting on or after January 1, 2020 (`AREA[StartDate]RANGE[2020-01-01,MAX]`).
    
- **Lead Sponsor Type**: Filtered to industry-sponsored trials only (`AREA[LeadSponsorClass]INDUSTRY`).

### 2. In-Memory & Parsing Filters (`api_call.py`)

During data extraction and DataFrame construction:

- **Intervention Type (Extraction)**: Interventions are filtered so that only interventions with a type of `"DRUG"` or `"BIOLOGICAL"` are captured in `drug_interventions` and `drug_and_other_names`.
    
- **Duplicate NCT IDs per Seed Term**: A `seen` set checks `nct_id` to prevent duplicate study entries from being added during a single seed term fetch.
    
- **Phase Exclusion**: Filters out trials where the phase is marked as `'NA'`.

### 3. Pipeline & Indication Filters (`main.py` & `disease_filter.py`)

After combining the datasets from all seed terms:

- **Cardiovascular Specific Filter**: A broad filter is applied to Cardiovascular Diseases by excluding any trial that contains any of the below indications in it's MeSH terms column.
	<details>
	<summary>Cardiovascular Broad Filters (Click the arrow to view)</summary>

	**Hematologic & Blood Protein:**  
	Hemostatic Disorders, Blood Protein Disorders, Cryoglobulinemia, Disseminated Intravascular Coagulation, Purpura, Purpura, Thrombocytopenic, Purpura, Hyperglobulinemic, Shwartzman Phenomenon, Angioedemas, Hereditary, Hemorrhoids  
	
	 **Oncologic & Neoplastic:**  
	  Multiple Myeloma, Leukemia, Plasma Cell, Plasmacytoma, Waldenstrom Macroglobulinemia, Hemangioma, Hemangioma, Cavernous, Neoplastic Syndromes, Hereditary  
	
	**Genetic, Metabolic, & Storage:**   
	Fabry Disease, Fabry Disease, Cardiac Variant, Amyloidosis, Gaucher Disease, Tangier Disease, Diabetic Angiopathies, Diabetic Retinopathy, Diabetic Foot, Scurvy   
	
	**Connective-Tissue & Autoimmune:**   
	Marfan Syndrome, Ehlers-Danlos Syndrome, Pseudoxanthoma Elasticum, Sarcoidosis, Lupus Erythematosus, Systemic, Telangiectasia, Hereditary Hemorrhagic   
	
	**Infectious:**   
	Syphilis, Cardiovascular, Tuberculosis, Cardiovascular
	
	</details>
    
- **Narrow Indication Filter**: Ran across the concatenated DataFrame to remove crossover/non-relevant trials by filtering if a single specific MeSH term is present per seed term indication.
	<details>
	<summary>Narrow Filters (Click the arrow to view)</summary>
	
	**Cardiovascular Diseases:**
	Diabetes Mellitus, Type 2, Renal Insufficiency, Chronic, Obesity, Diabetes Mellitus, Overweight, COVID-19
	
	**Autoimmune Diseases:**
	Diabetes Mellitus, Type 1, Diabetes Mellitus, Type 2, Diabetes Mellitus, Kidney Diseases, Renal Insufficiency, Chronic
	
	**Kidney Diseases:**
	Diabetes Mellitus, Type 1, Diabetes Mellitus, Type 2, Diabetes Mellitus, Autoimmune Diseases, Hypertension, Obesity, Heart Failure, COVID-19, Overweight
	
	**Liver Diseases:**
	Diabetes Mellitus, Type 1, Diabetes Mellitus, Type 2, Diabetes Mellitus, Autoimmune Diseases, Obesity, Overweight, Melanoma, Colorectal Neoplasms, Stomach Neoplasms, Ovarian Neoplasms, Breast Neoplasms, Lung Neoplasms, Pancreatic Neoplasms
	
	**Obesity:**
	Diabetes Mellitus, Type 1, Diabetes Mellitus, Type 2, Diabetes Mellitus, Non-alcoholic Fatty Liver Disease, Renal Insufficiency, Chronic
	
	**Diabetes Mellitus:**
	Obesity, Overweight, Renal Insufficiency, Chronic, Hypertension, Kidney Diseases, Retinal Diseases
	
	</details>
    
- **Device Intervention Exclusion**: Removes any study where the `intervention_type` string contains `"device"` (case-insensitive).
    

### 4. Global Denominators Scoring Filter (`scoring.py`)

When calculating global trial counts for scoring (`fetch_global_denominators_batch`):

- **Start Date**: Only includes studies starting 2020-01-01 or later (`AREA[StartDate]RANGE[2020-01-01,MAX]`).
    
- **Phases**: Filtered strictly to early stages (`AREA[Phase](EARLY_PHASE1 OR PHASE1 OR PHASE2)`).
    
- **Trial Status**: Restricted to active overall statuses (`RECRUITING`, `NOT_YET_RECRUITING`, `ACTIVE_NOT_RECRUITING`, `ENROLLING_BY_INVITATION`).
## CSV Files Breakdown
### all_diseases.csv
This is the master dataset containing all clinical trials retrieved across the specified indication categories (the 7 seed terms) after all exclusion filters, deduplication, and sponsor normalizations have been applied.   

**Schema (Columns):**  
The majority of columns are self explanatory.  
- `seed_term`: Term used to query ClinicalTrials.gov
- `status` and `study_status` provide the same information, but is included for any Tableau dashboard updates.
- `conditions`: Conditions submitted by the sponsor or party responsible for registering the trial.
- `drug_interventions`: List of drug names with their type in parenthesis next to the name.  
	Ex: Sotatercept (BIOLOGICAL) | Placebo (DRUG)
- `drug_and_other_names`: List of drug names separated by `|` with the first alias next to it with `:::` and any subsequent aliases with `::`.  
	Ex: rhGM-CSF + hydrogel ::: Repogel :: Molgramostim | Placebo hydrogel
- `mesh_ancestors`: Ancestor MeSH terms that are higher up in the hierarchical MeSH tree of the assigned MeSH terms in `mesh_terms`.
- `sponsor_norm` and `parent_sponsor`: Sponsor normalization using `industry_norm_final.csv` to map normalized sponsors and parent sponsors. Defaults to `sponsor` column value if the sponsor is not found in `industry_norm_final.csv`.
- `global_trial_count`: A total count of trials across all indications that are considered in the early phase and active status defined in the [filtered section](#4-global-denominators-scoring-filter-scoringpy) for a sponsor.  
		(*Note*: This column is not present when asking for 'one' CSV file to be updated from the Python program as it is only used for the scoring system.)
### weight_scoring.csv
This file contains the quantitative evaluation of the industry sponsors based on their post-2020 clinical trial portfolios. It serves as the output of the mathematical engine located in `scoring.py`.
### mesh_mapping.csv
A relational mapping table of individual MeSH terms to NCT ID for the purpose of being able to filter by single MeSH terms in Tableau.
### industry_norm_final.csv
A relational mapping table of raw sponsor names to normalized sponsor and parent sponsor names.  
(*Note*: This CSV file never updates as it was created with AI prompts and manually checks. Any new sponsor names or variations in spelling will not be correctly normalized.)
