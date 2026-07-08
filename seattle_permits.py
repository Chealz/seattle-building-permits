import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------------------------------------
# Page Configuration
# ------------------------------------------------
st.set_page_config(
    page_title="Seattle Building Permits Analysis",
    page_icon="🏗️",
    layout="wide"
)

# ------------------------------------------------
# Title
# ------------------------------------------------
st.title("🏗️ Seattle Building Permits Analysis")

st.markdown("""
Explore historical **Seattle building permit activity** using interactive filters.

Use the slider below to analyze how permit activity changed over time.
""")

st.info("Select a year range to explore permit trends across Seattle.")

# ------------------------------------------------
# Load Data
# ------------------------------------------------
df = pd.read_csv("Building_Permits.csv")

# Clean dates
df["IssuedDate"] = pd.to_datetime(df["IssuedDate"], errors="coerce")
df = df.dropna(subset=["IssuedDate"])

# Create Year column
df["Year"] = df["IssuedDate"].dt.year

# ------------------------------------------------
# Sidebar
# ------------------------------------------------
st.sidebar.header("Filters")

year_range = st.sidebar.slider(
    "Select Year Range",
    min_value=int(df["Year"].min()),
    max_value=int(df["Year"].max()),
    value=(2015, 2023)
)

# ------------------------------------------------
# Filter Data
# ------------------------------------------------
filtered_df = df[
    (df["Year"] >= year_range[0]) &
    (df["Year"] <= year_range[1])
]

permits_per_year = (
    filtered_df["Year"]
    .value_counts()
    .sort_index()
    .reset_index()
)

permits_per_year.columns = ["Year", "Permits"]

# ------------------------------------------------
# KPI Cards
# ------------------------------------------------
total_permits = len(filtered_df)

average_permits = int(permits_per_year["Permits"].mean())

highest_row = permits_per_year.loc[
    permits_per_year["Permits"].idxmax()
]

col1, col2, col3 = st.columns(3)

col1.metric(
    "📄 Total Permits",
    f"{total_permits:,}"
)

col2.metric(
    "📊 Average Per Year",
    f"{average_permits:,}"
)

col3.metric(
    "🏆 Highest Year",
    str(int(highest_row["Year"])),
    f'{highest_row["Permits"]:,} permits'
)

st.markdown("---")

st.write(
    f"Showing permit data from **{year_range[0]}** through **{year_range[1]}**."
)

# ------------------------------------------------
# Interactive Chart
# ------------------------------------------------
st.subheader("Permits Issued Per Year")

fig = px.bar(
    permits_per_year,
    x="Year",
    y="Permits",
    title="Seattle Building Permits Issued Per Year",
    labels={
        "Year": "Year",
        "Permits": "Number of Permits"
    },
    text_auto=True
)

fig.update_layout(
    xaxis_title="Year",
    yaxis_title="Number of Permits",
    hovermode="x unified",
    height=550
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ------------------------------------------------
# Data Table
# ------------------------------------------------
with st.expander("📋 View Filtered Data"):

    st.dataframe(
        filtered_df,
        use_container_width=True
    )

# ------------------------------------------------
# Summary
# ------------------------------------------------
st.subheader("Summary")

st.write(f"""
Between **{year_range[0]}** and **{year_range[1]}**, the dataset contains
**{total_permits:,} building permits**.

The highest number of permits occurred in **{int(highest_row['Year'])}**
with **{highest_row['Permits']:,} permits**.
""")

# ------------------------------------------------
# Footer
# ------------------------------------------------
st.markdown("---")

st.caption(
    "Data Source: City of Seattle Open Data Portal – Building Permits"
)