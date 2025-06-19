import pandas as pd

# Player data
player_data = [
    {"Posisi": "DF", "Nama Pemain": "Eric Abidal", "Goal/90": 0.00, "Assist/90": 0.04},
    {"Posisi": "DF", "Nama Pemain": "Javier Mascherano", "Goal/90": 0.00, "Assist/90": 0.00},
    {"Posisi": "DF", "Nama Pemain": "Carles Puyol", "Goal/90": 0.10, "Assist/90": 0.00},
    {"Posisi": "DF", "Nama Pemain": "Dani Alves", "Goal/90": 0.05, "Assist/90": 0.31},
    {"Posisi": "DM", "Nama Pemain": "Sergio Busquets", "Goal/90": 0.05, "Assist/90": 0.03},
    {"Posisi": "CM", "Nama Pemain": "Xavi", "Goal/90": 0.34, "Assist/90": 0.22},
    {"Posisi": "CM", "Nama Pemain": "Andres Iniesta", "Goal/90": 0.19, "Assist/90": 0.37},
    {"Posisi": "FW", "Nama Pemain": "Pedro", "Goal/90": 0.38, "Assist/90": 0.13},
    {"Posisi": "FW", "Nama Pemain": "Lionel Messi", "Goal/90": 1.35, "Assist/90": 0.44},
    {"Posisi": "FW", "Nama Pemain": "Cesc Fabregas", "Goal/90": 0.35, "Assist/90": 0.35}
]

df = pd.DataFrame(player_data)

# Position weight matrix
position_weights = {
    "DF": {"DF": 0.05, "DM": 0.35, "CM": 0.25, "FW": 0.10},
    "DM": {"DF": 0.10, "DM": 0.00, "CM": 0.50, "FW": 0.35},
    "CM": {"DF": 0.05, "DM": 0.25, "CM": 0.40, "FW": 0.70},
    "FW": {"DF": 0.05, "DM": 0.15, "CM": 0.45, "FW": 0.60}
}

# Calculate team statistics
avg_contribution = (df["Goal/90"].sum() + df["Assist/90"].sum()) / len(df)
min_connection = 0.1  # Minimum connection value

def calculate_pass_weight(passer, receiver):
    """Calculate pass weight between two players"""
    pos_passer = passer["Posisi"]
    pos_receiver = receiver["Posisi"]
    
    # Get position weight
    pos_weight = position_weights.get(pos_passer, {}).get(pos_receiver, 0.05)
    
    # Calculate relative contribution
    contribution = ((passer["Assist/90"] + receiver["Goal/90"]) / avg_contribution) + min_connection
    
    return round(pos_weight * contribution, 2)

# Create weight matrix
pass_weights = pd.DataFrame(index=df["Nama Pemain"], 
                          columns=df["Nama Pemain"],
                          dtype=float)

# Fill weight matrix
for _, passer in df.iterrows():
    for _, receiver in df.iterrows():
        if passer["Nama Pemain"] == receiver["Nama Pemain"]:
            pass_weights.loc[passer["Nama Pemain"], receiver["Nama Pemain"]] = 0
        else:
            weight = calculate_pass_weight(passer, receiver)
            pass_weights.loc[passer["Nama Pemain"], receiver["Nama Pemain"]] = weight

# Function to filter realistic Tiki-Taka connections
def is_realistic_connection(passer, receiver, weight):
    """Determine if connection is realistic for Tiki-Taka"""
    passer_pos = df.loc[df["Nama Pemain"] == passer, "Posisi"].values[0]
    receiver_pos = df.loc[df["Nama Pemain"] == receiver, "Posisi"].values[0]
    
    # Exclude direct DF→FW passes (except Dani Alves)
    if passer_pos == "DF" and receiver_pos == "FW" and passer != "Dani Alves":
        return False
        
    # Include key Tiki-Taka patterns
    if weight >= 0.3:  # Strong connections always included
        return True
        
    # Include important midfield connections even if slightly weaker
    if (passer_pos in ["CM", "DM"] and receiver_pos in ["CM", "FW"]) and weight >= 0.2:
        return True
        
    # Include defensive connections for continuity
    if (passer_pos in ["DF", "DM"] and receiver_pos in ["DM", "CM"]) and weight >= 0.1:
        return True
        
    return False

# Get realistic connections
realistic_connections = []
for passer in df["Nama Pemain"]:
    for receiver in df["Nama Pemain"]:
        if passer != receiver:
            weight = pass_weights.loc[passer, receiver]
            if is_realistic_connection(passer, receiver, weight):
                realistic_connections.append({
                    "From": passer,
                    "To": receiver,
                    "Weight": weight,
                    "From Position": df.loc[df["Nama Pemain"] == passer, "Posisi"].values[0],
                    "To Position": df.loc[df["Nama Pemain"] == receiver, "Posisi"].values[0]
                })

# Convert to DataFrame
connections_df = pd.DataFrame(realistic_connections)

# Sort by weight descending
connections_df = connections_df.sort_values("Weight", ascending=False)

# Display function
def display_connections(title, dataframe):
    print(f"\n{title}")
    print("="*(len(title)+5))
    # Display only the most important columns
    display_cols = ["From", "From Position", "To", "To Position", "Weight"]
    print(dataframe[display_cols].to_markdown(tablefmt="grid", stralign="center", numalign="center"))
    print("\n")

# Display player statistics
print("\nPlayer Statistics:")
print("="*20)
print(df[["Nama Pemain", "Posisi", "Goal/90", "Assist/90"]].to_markdown(tablefmt="grid", stralign="center", numalign="center"))

# Display realistic connections
display_connections("Realistic Tiki-Taka Connections (Weight ≥ 0.3)", 
                   connections_df[connections_df["Weight"] >= 0.3])

display_connections("Supporting Connections (0.1 ≤ Weight < 0.3)", 
                   connections_df[(connections_df["Weight"] >= 0.1) & (connections_df["Weight"] < 0.3)])

# Display key player degrees
print("\nKey Player Connection Counts:")
print("="*30)
degree_out = connections_df["From"].value_counts().reset_index()
degree_in = connections_df["To"].value_counts().reset_index()
degree_out.columns = ["Player", "Connection Count"]
degree_in.columns = ["Player", "Connection Count"]
print("\n Degree Out : ")
print(degree_out.to_markdown(tablefmt="grid", stralign="center", index=False))
print("\n Degree In : ")
print(degree_in.to_markdown(tablefmt="grid", stralign="center", index=False))

# Function to adjust weights when Messi is marked and show alternatives only for significant passers to Messi
def adjust_marked_messi_with_filtered_alternatives(df, pass_weights, marking_intensity=0.7, min_messi_weight=0.3):

    adjusted_weights = pass_weights.copy()
    messi = "Lionel Messi"
    
    # Get players who originally passed significantly to Messi
    significant_passers = pass_weights[messi][pass_weights[messi] >= min_messi_weight].index.tolist()
    
    # Adjust weights to Messi
    for passer in df["Nama Pemain"]:
        if passer != messi:
            original_weight = adjusted_weights.loc[passer, messi]
            adjusted_weight = original_weight * (1 - marking_intensity)
            adjusted_weights.loc[passer, messi] = adjusted_weight
    
    # Get alternative passing options only for significant passers
    alternative_passes = {}
    for passer in significant_passers:
        # Get all possible receivers except self and Messi, sorted by weight descending
        options = adjusted_weights.loc[passer].drop([passer, messi]).sort_values(ascending=False)
        alternative_passes[passer] = options
            
    return adjusted_weights, alternative_passes

# Apply marking with filtered alternatives (only show alternatives for players with original weight to Messi >= 0.3)
marked_weights_filtered, alternative_passes_filtered = adjust_marked_messi_with_filtered_alternatives(df, pass_weights)

# Display adjusted weights to Messi for significant passers only
print("\nAdjusted Pass Weights to Messi for Significant Passers (Original Weight ≥ 0.3):")
print("="*70)
significant_messi_weights = marked_weights_filtered.loc[pass_weights["Lionel Messi"] >= 0.3, "Lionel Messi"].sort_values(ascending=False)
print(significant_messi_weights.to_markdown(tablefmt="grid", stralign="center"))

# Display alternative passing options only for significant passers to Messi
print("\nAlternative Passing Options for Players Who Originally Had Strong Connection to Messi (Weight ≥ 0.3):")
print("="*90)
for passer, options in alternative_passes_filtered.items():
    original_weight = pass_weights.loc[passer, "Lionel Messi"]
    print(f"\n{passer} (Position: {df[df['Nama Pemain'] == passer]['Posisi'].values[0]})")
    print(f"Original weight to Messi: {original_weight:.2f} → Adjusted weight: {original_weight * 0.3:.2f}")
    print("-"*(len(passer) + 30))
    print("Top 3 Alternatives:")
    print(options.head(3).to_markdown(tablefmt="grid", stralign="center"))

# Create marked connections dataframe
marked_connections_filtered = []
for passer in df["Nama Pemain"]:
    for receiver in df["Nama Pemain"]:
        if passer != receiver:
            weight = marked_weights_filtered.loc[passer, receiver]
            if is_realistic_connection(passer, receiver, weight):
                marked_connections_filtered.append({
                    "From": passer,
                    "To": receiver,
                    "Weight": weight,
                    "From Position": df.loc[df["Nama Pemain"] == passer, "Posisi"].values[0],
                    "To Position": df.loc[df["Nama Pemain"] == receiver, "Posisi"].values[0]
                })

marked_connections_filtered_df = pd.DataFrame(marked_connections_filtered).sort_values("Weight", ascending=False)

# Show network changes for significant passers
print("\nNetwork Changes for Significant Passers to Messi:")
print("="*60)
significant_passers_df = df[df["Nama Pemain"].isin(alternative_passes_filtered.keys())]
print("\nPlayers Affected by Messi Marking (Original Weight to Messi ≥ 0.3):")
print(significant_passers_df[["Nama Pemain", "Posisi", "Assist/90"]].to_markdown(tablefmt="grid", stralign="center"))

# Show their new strongest connections
print("\nTheir New Strongest Connections After Messi is Marked:")
for passer in alternative_passes_filtered.keys():
    passer_connections = marked_connections_filtered_df[
        (marked_connections_filtered_df["From"] == passer) & 
        (marked_connections_filtered_df["To"] != "Lionel Messi")
    ].head(3)
    
    if not passer_connections.empty:
        print(f"\n{passer}'s new top connections:")
        print(passer_connections[["To", "To Position", "Weight"]].to_markdown(tablefmt="grid", stralign="center", index=False))