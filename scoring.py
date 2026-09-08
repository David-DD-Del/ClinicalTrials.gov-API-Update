import pandas as pd
import numpy as np
import requests
import data_utils
from tqdm import tqdm
from sklearn.linear_model import LinearRegression

ACTIVE_STATUSES = {
    "NOT_YET_RECRUITING", "RECRUITING",
    "ENROLLING_BY_INVITATION", "ACTIVE_NOT_RECRUITING",
}

EARLY_PHASE_TERMS = {
    "EARLY_PHASE1", "PHASE1", "PHASE2",
    "Early Phase 1", "Phase 1", "Phase 2",
}

def contains_any(text, terms):
    text = str(text).lower()
    return any(str(t).lower() in text for t in terms)

def sponsor_indication_activity(g):
    h = g.drop_duplicates("nct_id")
    return pd.Series({
        "total_trials_since_2020": h["nct_id"].nunique(),
        "active_trials_since_2020": h.loc[h["is_active"], "nct_id"].nunique(),
        "early_phase_trials_since_2020": h.loc[h["is_early_phase"], "nct_id"].nunique(),
        "active_early_trials_since_2020": h.loc[h["is_active_early"], "nct_id"].nunique(),
    })

def trial_activity_scoring(df):
    df["start_dt"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["start_year"] = df["start_dt"].dt.year
    df["is_active"] = df["study_status"].isin(ACTIVE_STATUSES)
    df["is_early_phase"] = df["phases"].apply(lambda x: contains_any(x, EARLY_PHASE_TERMS))
    df["is_active_early"] = df["is_active"] & df["is_early_phase"]

    # 2. Now create your isolated local copy for the deduplication and grouping
    local_df = df.drop_duplicates(["seed_term", "sponsor", "nct_id"])

    # 3. Use 'local_df' for the grouping step instead of 'df'
    score = (
        local_df.groupby(["seed_term", "sponsor"])
        .apply(sponsor_indication_activity, include_groups=False)
        .reset_index()
    )

    activity_cols = [
        "total_trials_since_2020",
        "active_trials_since_2020",
        "early_phase_trials_since_2020",
        "active_early_trials_since_2020",
    ]

    # Identify rare-disease seed terms
    rare_by_seed = (
        score["seed_term"]
        .astype(str)
        .str.lower()
        .str.contains("rare", na=False)
    )


    for col in activity_cols:

        # P95 cap for standard indications
        p95_cap = (
            score.groupby("seed_term")[col]
            .transform(
                lambda x: x.quantile(0.95)
            )
        )

        # Maximum cap for rare indications
        max_cap = (
            score.groupby("seed_term")[col]
            .transform("max")
        )

        # Select appropriate cap
        cap = p95_cap.where(
            ~rare_by_seed,
            max_cap
        )

        # Normalize
        score[f"{col}_score"] = (
            score[col]
            .clip(lower=0)
            .div(
                cap.replace(0, np.nan)
            )
            .clip(upper=1)
            .fillna(0.0)
        )

    # Hierarchical blend — active early-phase dominates
    score["trial_activity_score"] = (
        0.65 * score["active_early_trials_since_2020_score"] +
        0.15 * score["early_phase_trials_since_2020_score"] +
        0.15 * score["active_trials_since_2020_score"] +
        0.05 * score["total_trials_since_2020_score"]
    )

    return score

def therapeutic_focus_scoring(df, th_score):
    # 1. Extract a unique mapping of sponsor to global trial count from df
    sponsor_total_active_early = (
        df[["sponsor", "global_trial_count"]]
        .drop_duplicates("sponsor")
        .rename(columns={"global_trial_count": "sponsor_total_active_early"})
    )

    # 2. Merge it into your score dataframe on the raw 'sponsor' column
    th_score = th_score.merge(sponsor_total_active_early, on="sponsor", how="left", validate="many_to_one")

    # 3. Calculate the therapeutic focus score
    th_score["therapeutic_focus_score"] = np.where(
        th_score["sponsor_total_active_early"] > 0,
        th_score["active_early_trials_since_2020"] / th_score["sponsor_total_active_early"],
        0.0
    )

    return th_score


def activity_trajec_scoring(df, at_score):
    # 1. Isolate the base trials containing valid datetime objects
    time_base_df = df.dropna(subset=["start_dt"]).drop_duplicates(["seed_term", "sponsor", "nct_id"]).copy()

    # ---------------------------------------------------------
    # A. Recent vs Early Period (Exact Date Cutoffs)
    # ---------------------------------------------------------
    # Early: Jan 1, 2020 - June 30, 2023
    # Recent: July 1, 2023 - Current
    time_base_df["is_early_period"] = time_base_df["start_dt"].between("2020-01-01", "2023-06-30")
    time_base_df["is_recent_period"] = time_base_df["start_dt"] >= "2023-07-01"


    def recent_vs_early_exact(g):
        early = g["is_early_period"].sum()
        recent = g["is_recent_period"].sum()
        # Tanh smoothing to prevent explosion from small bases (0 to 1 trial)
        growth = 0.5 + 0.5 * np.tanh(np.log((recent + 1) / (early + 1)))

        return pd.Series({
            "starts_early_period": early,
            "starts_recent_period": recent,
            "recent_vs_early_score": growth,
        })


    growth_period = (
        time_base_df.groupby(["seed_term", "sponsor"])
        .apply(recent_vs_early_exact, include_groups=False)
        .reset_index()
    )

    # ---------------------------------------------------------
    # B. Linear Regression Slope (Yearly Trend)
    # ---------------------------------------------------------
    year_min = 2020
    year_max = int(time_base_df["start_year"].max()) if not time_base_df["start_year"].isna().all() else 2024
    year_grid = list(range(year_min, year_max + 1))

    yearly = (
        time_base_df.groupby(["seed_term", "sponsor", "start_year"])["nct_id"]
        .nunique()
        .reset_index(name="trial_starts")
    )

    # Fill missing years with 0 safely using 'yearly'
    if not yearly.empty:
        idx = pd.MultiIndex.from_product(
            [yearly["seed_term"].unique(), yearly["sponsor"].unique(), year_grid],
            names=["seed_term", "sponsor", "start_year"]
        )
        yearly_full = (
            yearly.set_index(["seed_term", "sponsor", "start_year"])
            .reindex(idx, fill_value=0)
            .reset_index()
        )
    else:
        yearly_full = yearly.copy()


    def slope_score(g):
        x = g["start_year"].to_numpy().reshape(-1, 1)
        y = g["trial_starts"].to_numpy()
        if y.sum() == 0:
            return pd.Series({"start_slope": 0.0})
        model = LinearRegression().fit(x, y)
        return pd.Series({"start_slope": model.coef_[0]})


    slopes = (
        yearly_full.groupby(["seed_term", "sponsor"])
        .apply(slope_score)
        .reset_index()
    )


    def slope_to_score(s):
        lo = s.quantile(0.05)
        hi = s.quantile(0.95)
        if hi == lo or pd.isna(lo) or pd.isna(hi):
            return pd.Series(0.5, index=s.index)
        return ((s.clip(lo, hi) - lo) / (hi - lo)).clip(0, 1)


    if "start_slope" in slopes.columns:
        slopes["slope_score"] = (
            slopes.groupby("seed_term")["start_slope"]
            .transform(slope_to_score)
        )
    else:
        slopes["slope_score"] = 0.5

    # ---------------------------------------------------------
    # C. Build Composite Trajectory Score Safely
    # ---------------------------------------------------------

    # SAFETY CHECK 1: Ensure columns exist in 'slopes' before the first merge
    slope_merge_cols = ["seed_term", "sponsor", "start_slope", "slope_score"]
    for c in slope_merge_cols:
        if c not in slopes.columns:
            slopes[c] = np.nan

    trajectory = growth_period.merge(
        slopes[slope_merge_cols],
        on=["seed_term", "sponsor"],
        how="left"
    )

    # Safely extract or fill scores
    trajectory["recent_vs_early_score"] = trajectory.get("recent_vs_early_score", pd.Series(dtype=float)).fillna(0.5)
    trajectory["slope_score"] = trajectory.get("slope_score", pd.Series(dtype=float)).fillna(0.5)

    trajectory["activity_trajectory_score"] = (
            0.60 * trajectory["recent_vs_early_score"] +
            0.40 * trajectory["slope_score"]
    )

    # SAFETY CHECK 2: Guarantee the columns exist before the final merge subset to avoid KeyError
    final_merge_cols = ["seed_term", "sponsor", "activity_trajectory_score", "start_slope", "starts_early_period",
                        "starts_recent_period"]
    for c in final_merge_cols:
        if c not in trajectory.columns:
            trajectory[c] = np.nan

    # Defensive index reset on 'score' dataframe just in case
    if "seed_term" not in at_score.columns or "sponsor" not in at_score.columns:
        at_score = at_score.reset_index()

    # Merge cleanly into main score DataFrame
    at_score = at_score.merge(
        trajectory[final_merge_cols],
        on=["seed_term", "sponsor"],
        how="left"
    )

    # Final safety fill for missing data
    at_score["activity_trajectory_score"] = at_score.get("activity_trajectory_score", pd.Series(dtype=float)).fillna(0.5)

    return at_score


def breadth_scoring(df, b_score):
    breadth_base = (
        df[df["is_active_early"]]
        .drop_duplicates(["sponsor", "nct_id", "seed_term"])
    )

    indication_counts = (
        breadth_base
        .groupby(["sponsor", "seed_term"])["nct_id"]
        .nunique()
        .reset_index(name="trial_count")
    )

    def effective_breadth(counts):
        vals = counts.to_numpy(dtype=float)
        if vals.sum() == 0:
            return 0.0
        p = vals / vals.sum()
        return 1 / np.sum(p ** 2)   # inverse Herfindahl index

    breadth = (
        indication_counts
        .groupby("sponsor")["trial_count"]
        .apply(effective_breadth)
        .reset_index(name="effective_indication_breadth")
    )

    B_sat = max(2.0, breadth["effective_indication_breadth"].quantile(0.95))

    breadth["breadth_score"] = np.minimum(
        1.0,
        np.log1p(breadth["effective_indication_breadth"]) / np.log1p(B_sat)
    )

    b_score = b_score.merge(breadth, on="sponsor", how="left")
    b_score["breadth_score"] = b_score["breadth_score"].fillna(0.0)

    return b_score


def final_score(f_score):
    WEIGHTS = {
        "trial_activity_score":      0.50,
        "therapeutic_focus_score":   0.20,
        "activity_trajectory_score": 0.20,
        "breadth_score":             0.10,
    }

    f_score["prospect_score"] = 100 * sum(
        w * f_score[col] for col, w in WEIGHTS.items()
    )

    f_score = f_score.sort_values(
        ["seed_term", "prospect_score"],
        ascending=[True, False]
    )

    return f_score


def fetch_global_denominators_batch():
    url = "https://clinicaltrials.gov/api/v2/studies"
    all_sponsors = []

    # 1. Define the query for ALL post-2020 early-phase active trials
    params = {
        # THE FIX: Bundle both Date and Phase into the advanced Essie syntax
        "filter.advanced": "AREA[StartDate]RANGE[2020-01-01,MAX] AND AREA[Phase](EARLY_PHASE1 OR PHASE1 OR PHASE2)",

        "filter.overallStatus": "RECRUITING,NOT_YET_RECRUITING,ACTIVE_NOT_RECRUITING,ENROLLING_BY_INVITATION",
        "pageSize": 250,
    }

    print("Fetching global trial landscape in batches of 250...")

    # 1. Initialize the manual progress bar
    pbar = tqdm(desc="Batches Downloaded")

    while True:
        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(response.url)
            print(response.text)
            raise Exception("API request failed")

        # Parse the JSON payload
        data = response.json()

        # Extract the sponsor names from this batch
        for study in data.get('studies', []):
            try:
                raw_sponsor = study['protocolSection']['sponsorCollaboratorsModule']['leadSponsor']['name']
                all_sponsors.append(raw_sponsor.strip())
            except KeyError:
                continue

        # 2. Update the progress bar by 1 tick for every page successfully downloaded
        pbar.update(1)

        # Handle Pagination
        next_page_token = data.get('nextPageToken')
        if not next_page_token:
            break

        params['pageToken'] = next_page_token

    # 3. Close the progress bar when the loop finishes
    pbar.close()

    # 2. Let Pandas do the aggregation locally
    print(f"\nDownloaded {len(all_sponsors)} total trials. Calculating global denominators...")

    df_global = pd.DataFrame(all_sponsors, columns=['sponsor'])
    global_counts = df_global.groupby('sponsor').size().reset_index(name='global_trial_count')

    return global_counts

def scoring_system(master_df):
    # 1. Fetch the global denominators (now mapped to 'sponsor' with whitespace stripped)
    global_df = fetch_global_denominators_batch()

    # 2. Strip whitespace from your master_df just to be safe
    master_df['sponsor'] = master_df['sponsor'].str.strip()

    # 3. Perform the left merge directly on the raw 'sponsor' column
    master_df = master_df.merge(global_df, on='sponsor', how='left')

    # 4. Fill any missing values with 0
    master_df['global_trial_count'] = master_df['global_trial_count'].fillna(0).astype(int)

    # Verify it worked
    # print(master_df[['sponsor', 'global_trial_count']].head())

    df = master_df.copy()
    score = trial_activity_scoring(df)
    score = therapeutic_focus_scoring(df, score)
    score = activity_trajec_scoring(df, score)
    score = breadth_scoring(df, score)
    score = final_score(score)

    data_utils.save_csv(score, 'weight_scoring.csv')
    print("Scoring CSV written to: weight_scoring.csv")

    return master_df







