import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Load the data
df = pd.read_csv('user-answers.csv')
df['created_at'] = pd.to_datetime(df['created_at'])
df = df.dropna(subset=['answer']).copy()

# Standardize column mapping to strings to avoid indexing errors
df['answer_str'] = df['answer'].astype(str).str.upper()
df = df.sort_values('created_at')

# Define meeting dates
meeting_dates = pd.to_datetime([
    '2025-10-17', '2025-10-24', '2025-10-31', 
    '2025-11-07', '2025-11-14', '2025-11-21', '2025-11-28', 
    '2025-12-05', 
    '2026-01-09', '2026-01-16', '2026-01-30', 
    '2026-02-06', '2026-02-20', '2026-02-27', 
    '2026-03-06', '2026-03-13', '2026-03-23', '2026-03-30', 
    '2026-04-06'
])

def calculate_kappa_strict(subset_df, min_articles=None):
    """
    Calculates Fleiss' Kappa for articles with 2+ reviews.
    If min_articles is set, returns NaN if the article count is too low.
    """
    if subset_df.empty:
        return np.nan
    
    # Group by article and answer
    counts = subset_df.groupby(['article_id', 'answer_str']).size().unstack(fill_value=0)
    
    # Ensure columns exist
    for col in ['TRUE', 'FALSE']:
        if col not in counts.columns:
            counts[col] = 0
            
    # Filter: ONLY papers with 2 or more reviews
    n_i = counts[['TRUE', 'FALSE']].sum(axis=1)
    valid_counts = counts[n_i >= 2].copy()
    
    # THRESHOLD CHECK
    if min_articles and len(valid_counts) < min_articles:
        return np.nan
    
    if len(valid_counts) == 0:
        return np.nan
    
    n_i_v = valid_counts[['TRUE', 'FALSE']].sum(axis=1)
    sum_sq = (valid_counts[['TRUE', 'FALSE']]**2).sum(axis=1)
    Pi = (sum_sq - n_i_v) / (n_i_v * (n_i_v - 1))
    P_mean = Pi.mean()
    
    total_ratings = n_i_v.sum()
    p_true = valid_counts['TRUE'].sum() / total_ratings
    p_false = valid_counts['FALSE'].sum() / total_ratings
    Pe = p_true**2 + p_false**2
    
    if Pe >= 1.0: return 1.0
    return (P_mean - Pe) / (1 - Pe)

results = []
all_days = pd.date_range(start=df['created_at'].min().date(), end=df['created_at'].max().date(), freq='D')

# Set the threshold for "enough new articles"
MIN_ARTICLE_THRESHOLD = 50

for day in all_days:
    cutoff_end = pd.Timestamp(day).tz_localize('UTC') + pd.Timedelta(days=1)
    window_start = cutoff_end - pd.Timedelta(days=30)
    
    cumulative_subset = df[df['created_at'] < cutoff_end]
    rolling_subset = df[(df['created_at'] < cutoff_end) & (df['created_at'] >= window_start)]
    
    kappa_cum = calculate_kappa_strict(cumulative_subset)
    # Apply dynamic threshold to rolling kappa
    kappa_roll = calculate_kappa_strict(rolling_subset, min_articles=MIN_ARTICLE_THRESHOLD)
    
    total_reviews = len(cumulative_subset)
    
    results.append({
        'date': day,
        'kappa_cumulative': kappa_cum,
        'kappa_rolling': kappa_roll,
        'total_reviews': total_reviews
    })

res_df = pd.DataFrame(results).dropna(subset=['kappa_cumulative'])

# Plotting
fig, ax1 = plt.subplots(figsize=(15, 8))

# Plot Kappa Values
ax1.plot(res_df['date'], res_df['kappa_cumulative'], color='blue', linewidth=3, label="Cumulative Fleiss' Kappa")
# The rolling line will now have gaps where the data volume is too low
ax1.plot(res_df['date'], res_df['kappa_rolling'], color='cyan', linestyle='-', linewidth=2.5, label=f"30-Day Rolling Kappa (Min {MIN_ARTICLE_THRESHOLD} articles)")

ax1.set_xlabel('Date', fontsize=12)
ax1.set_ylabel("Fleiss' Kappa", color='blue', fontsize=12)
ax1.tick_params(axis='y', labelcolor='blue')
ax1.grid(True, linestyle='--', alpha=0.3)
ax1.set_ylim(0.6, 0.9)

# Secondary Axis: Cumulative Reviews
ax2 = ax1.twinx()
ax2.plot(res_df['date'], res_df['total_reviews'], color='purple', linestyle=':', alpha=0.5, linewidth=2, label="Cumulative Total Reviews")
ax2.set_ylabel('Cumulative Total Reviews', color='purple', fontsize=12)
ax2.tick_params(axis='y', labelcolor='purple')

# Add Meeting dates
for i, m_date in enumerate(meeting_dates):
    lbl = "Weekly Meeting" if i == 0 else ""
    ax1.axvline(m_date, color='red', linestyle='-', alpha=0.4, label=lbl)

plt.title("Dynamic Reliability Tracking: Robust Rolling Kappa vs. Cumulative Progress", fontsize=15, pad=20)

# Merge legends
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='lower right', frameon=True, shadow=True)

# Formatting
ax1.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=2))
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%Y'))

plt.tight_layout()
plt.savefig('dynamic_rolling_kappa.png')
print("Dynamic plot saved as dynamic_rolling_kappa.png")
res_df.to_csv('dynamic_rolling_data.csv', index=False)
