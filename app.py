import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="Seattle Building Permits Analysis",
    page_icon="🏗️",
    layout="wide"
)

# -----------------------------
# Title
# -----------------------------
st.title("🏗️ Seattle Building Permits Analysis")

st.write("""
Explore historical Seattle building permit activity using interactive filters.
Adjust the year range below to analyze permit trends over time.
""")

# Info Box
st.info("Use the slider below to explore how Seattle building permit activity has changed over time.")

# -----------------------------
# Load Data
# -----------------------------
df = pd.read_csv("Building_Permits.csv")

# Clean dates
df["IssuedDate"] = pd.to_datetime(df["IssuedDate"], errors="coerce")
df = df.dropna(subset=["IssuedDate"])
df["Year"] = df["IssuedDate"].dt.year

# -----------------------------
# Year Slider
# -----------------------------
year_range = st.slider(
    "Select Year Range",
    min_value=int(df["Year"].min()),
    max_value=int(df["Year"].max()),
    value=(2015, 2023)
)

# Filter data
filtered_df = df[
    (df["Year"] >= year_range[0]) &
    (df["Year"] <= year_range[1])
]

# Count permits
permits_per_year = filtered_df["Year"].value_counts().sort_index()

# -----------------------------
# Summary Metrics
# -----------------------------
total_permits = len(filtered_df)

average_permits = (
    int(permits_per_year.mean())
    if len(permits_per_year) > 0 else 0
)

highest_year = (
    permits_per_year.idxmax()
    if len(permits_per_year) > 0 else "N/A"
)

highest_value = (
    permits_per_year.max()
    if len(permits_per_year) > 0 else 0
)

col1, col2, col3 = st.columns(3)

col1.metric("📄 Total Permits", f"{total_permits:,}")
col2.metric("📊 Average Per Year", f"{average_permits:,}")
col3.metric("🏆 Highest Year", f"{highest_year}", f"{highest_value:,} permits")

st.markdown("---")

st.write(
    f"Showing permit data from **{year_range[0]}** through **{year_range[1]}**."
)

# -----------------------------
# Chart
# -----------------------------
st.subheader("Permits Issued Per Year")

fig, ax = plt.subplots(figsize=(11, 5))

sns.barplot(
    x=permits_per_year.index,
    y=permits_per_year.values,
    color="steelblue",
    ax=ax
)

ax.set_title("Seattle Building Permits Issued per Year", fontsize=14)
ax.set_xlabel("Year")
ax.set_ylabel("Number of Permits")

# Add grid lines for readability
ax.grid(axis="y", linestyle="--", alpha=0.5)

plt.xticks(rotation=45)
plt.tight_layout()

st.pyplot(fig)

# -----------------------------
# Data Preview
# -----------------------------
with st.expander("📋 View Filtered Data"):
    st.dataframe(filtered_df.head(100), use_container_width=True)

# -----------------------------
# Footer
# -----------------------------
st.markdown("---")

st.caption(
    "Data Source: City of Seattle Open Data Portal – Building Permits"
)