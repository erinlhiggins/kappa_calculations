import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def fleiss_kappa(ratings_matrix):
    """
    Calculates Fleiss' Kappa for a given ratings matrix.
    Rows are subjects (articles), columns are categories (True/False).
    Values are the count of raters who assigned that category to that subject.
    """
    N = ratings_matrix.shape[0]
    if N == 0: return np.nan
    n_raters = ratings_matrix.sum(axis=1)
    
    # Keep only articles with at least 2 reviews
    valid_idx = n_raters >= 2
    ratings_matrix = ratings_matrix[valid_idx]
    n_raters = n_raters[valid_idx]
    N = ratings_matrix.shape[0]
    
    if N == 0: return np.nan
    p_j = ratings_matrix.sum(axis=0) / ratings_matrix.sum()
    P_i = (np.sum(ratings_matrix**2, axis=1) - n_raters) / (n_raters * (n_raters - 1))
    P_bar = P_i.mean()
    P_e_bar = np.sum(p_j**2)
    
    if P_e_bar == 1: return 1.0
    kappa = (P_bar - P_e_bar) / (1 - P_e_bar)
    return kappa

def main():
    # 1. Load data
    df = pd.read_csv('user-answers.csv')
    df = df.dropna(subset=['answer'])
    # Standardize time handling
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_localize(None)

    # 2. Group by week
    df['review_week'] = df['created_at'].dt.to_period('W')
    unique_weeks = sorted(df['review_week'].unique())

    plot_weeks = []
    plot_kappas = []

    # 3. Calculate cumulative Kappa week-by-week
    for week in unique_weeks:
        current_reviews = df[df['review_week'] <= week]
        mat = pd.crosstab(current_reviews['article_id'], current_reviews['answer'])
        k = fleiss_kappa(mat.values)
        
        if not pd.isna(k):
            plot_weeks.append(week.start_time)
            plot_kappas.append(k)

    # 4. Generate the Plot
    fig, ax1 = plt.subplots(figsize=(12, 6))

    color = 'tab:blue'
    ax1.set_xlabel('Week')
    ax1.set_ylabel('Cumulative Kappa Score', color=color)
    ax1.plot(plot_weeks, plot_kappas, marker='o', linestyle='-', color=color, linewidth=2, label='Cumulative Kappa')
    ax1.tick_params(axis='y', labelcolor=color)
    
    # Focused scale
    ax1.set_ylim(0.7, 0.9)
    ax1.grid(True, linestyle='--', alpha=0.7)

    fig.autofmt_xdate(rotation=45)
    plt.title("Cumulative Reviewer Agreement (Full Timeline)")
    fig.tight_layout()

    # Save final figure
    plt.savefig('kappa_full_timeline_line_only.png', dpi=300)

if __name__ == "__main__":
    main()