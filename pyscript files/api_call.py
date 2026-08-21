import asyncio
import urllib.parse
import pandas as pd
from pyodide.http import pyfetch

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

async def fetch_trials(query):
    all_studies = []
    page_token = None

    while True:
        params = {
            "query.cond": query,
            "filter.advanced": "AREA[StartDate]RANGE[2020-01-01,MAX] AND AREA[LeadSponsorClass]INDUSTRY",
            "pageSize": 1000
        }

        if page_token:
            params["pageToken"] = page_token

        attempt = 0
        
        # Pyfetch requires the URL and parameters to be encoded together manually
        query_string = urllib.parse.urlencode(params)
        url = f"{BASE_URL}?{query_string}"

        try:
            # Swap requests.get for pyfetch
            r = await pyfetch(url, method="GET")

            if not r.ok:
                print(f"⚠️ API Request Failed! Status Code: {r.status}")
                break
            
            # await the JSON parsing
            data = await r.json()

            studies = data.get("studies", [])
            all_studies.extend(studies)

            # pagination control
            page_token = data.get("nextPageToken")

            if not page_token:
                break

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}. Retrying...")
            await asyncio.sleep(2)  # Non-blocking sleep
            attempt += 1

        if attempt > 4:
            raise Exception("ClinicalTrials.gov API failed to respond after multiple attempts.")

    return all_studies


async def run_pipeline(seed_term):
    seen = set()
    results = []

    print(f"\n=== Running: {seed_term} ===")
    
    # Await the fetch
    studies = await fetch_trials(seed_term)

    for study in studies:
        try:
            study_data = study.get("protocolSection", {})
            ident = study_data.get("identificationModule", {})
            status = study_data.get("statusModule", {})
            design = study_data.get("designModule", {})
            sponsors = study_data.get("sponsorCollaboratorsModule", {})
            desc = study_data.get("descriptionModule", {})
            conds = study_data.get("conditionsModule", {})
            interventions = study_data.get("armsInterventionsModule", {}).get("interventions", [])
            derived = study.get("derivedSection", {})
            cond_browse = derived.get("conditionBrowseModule", {})

            meshes = cond_browse.get("meshes", [])
            mesh_terms = [m.get("term", "") for m in meshes if m.get("term")]

            ancestors = cond_browse.get("ancestors", [])
            ancestor_terms = [a.get("term", "") for a in ancestors if a.get("term")]

            collaborator_names = [c.get("name", "") for c in sponsors.get("collaborators", []) if c.get("name")]

            interventions_list = []
            paired_names = []

            for inv in interventions:
                primary = inv.get("name")
                inv_type = inv.get("type", "").upper()

                if primary and inv_type in ["DRUG", "BIOLOGICAL"]:
                    interventions_list.append(f"{primary} ({inv_type})")
                    aliases = inv.get("otherNames", [])
                    if aliases:
                        alias_str = " :: ".join(aliases)
                        paired_names.append(f"{primary} ::: {alias_str}")
                    else:
                        paired_names.append(primary)

            nct_id = ident.get("nctId")

            if nct_id and nct_id not in seen:
                seen.add(nct_id)
                results.append({
                    "seed_term": seed_term,
                    "nct_id": nct_id,
                    "study_type": design.get("studyType"),
                    "status": status.get("overallStatus"),
                    "study_title": ident.get("briefTitle", ""),
                    "acronym": ident.get("acronym", ""),
                    "study_status": status.get("overallStatus", ""),
                    "brief_summary": desc.get("briefSummary", ""),
                    "conditions": ", ".join(conds.get("conditions", [])),
                    "sponsor": sponsors.get("leadSponsor", {}).get("name", ""),
                    "phases": ", ".join(design.get("phases", [])),
                    "funder_type": sponsors.get("leadSponsor", {}).get("class", ""),
                    "start_date": status.get("startDateStruct", {}).get("date", ""),
                    "completion_date": status.get("completionDateStruct", {}).get("date", ""),
                    "collaborators": ", ".join(collaborator_names),
                    "intervention_type": " | ".join(
                        list(set([inv.get("type", "") for inv in interventions if inv.get("type")]))),
                    "drug_interventions": " | ".join(interventions_list),
                    "drug_and_other_names": " | ".join(paired_names),
                    "mesh_terms": " | ".join(mesh_terms),
                    "mesh_ancestors": " | ".join(ancestor_terms)
                })

        except Exception as e:
            print(e)
            continue

    # Non-blocking sleep
    await asyncio.sleep(1.5)

    print(f"Found {len(results)} rows")
    df_results = pd.DataFrame(results)
    df_results = df_results[df_results['phases'] != 'NA']

    return df_results