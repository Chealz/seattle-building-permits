import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# Streamlit renamed use_container_width -> width="stretch" in v1.46.
# Support both so the app runs on any recent version.
_ST_VERSION = tuple(int(p) for p in st.__version__.split(".")[:2])
_STRETCH = (
    {"width": "stretch"} if _ST_VERSION >= (1, 46)
    else {"use_container_width": True}
)
# st.metric(border=...) needs Streamlit >= 1.41
_METRIC_KW = {"border": True} if _ST_VERSION >= (1, 41) else {}

# ------------------------------------------------
# Page Configuration
# ------------------------------------------------
st.set_page_config(
    page_title="Seattle Building Permits Analysis",
    page_icon="🏗️",
    layout="wide",
)

st.title("🏗️ Seattle Building Permits Analysis")
st.markdown(
    "Explore historical **Seattle building permit activity** with the filters "
    "in the sidebar."
)


# ------------------------------------------------
# Load Data — live from the Seattle Open Data API (Socrata),
# cached for 24h. Falls back to a local CSV if the API is down.
# ------------------------------------------------
API_URL = "https://data.seattle.gov/resource/76t5-zqzr.json"
LOCAL_CSV = "Building_Permits.csv"

# API (lowercase) -> app column names
FIELDS = {
    "permitnum": "PermitNum",
    "permitclassmapped": "PermitClassMapped",
    "permittypemapped": "PermitTypeMapped",
    "description": "Description",
    "housingunitsadded": "HousingUnitsAdded",
    "housingunitsremoved": "HousingUnitsRemoved",
    "estprojectcost": "EstProjectCost",
    "issueddate": "IssuedDate",
    "statuscurrent": "StatusCurrent",
    "originaladdress1": "OriginalAddress1",
    "latitude": "Latitude",
    "longitude": "Longitude",
}

NUMERIC_COLS = [
    "HousingUnitsAdded", "HousingUnitsRemoved",
    "EstProjectCost", "Latitude", "Longitude",
]

PAGE_SIZE = 50_000


def fetch_from_api() -> pd.DataFrame:
    """Page through the full dataset via SoQL. An app token isn't required,
    but setting the SOCRATA_APP_TOKEN env var avoids throttling."""
    headers = {}
    if token := os.environ.get("SOCRATA_APP_TOKEN"):
        headers["X-App-Token"] = token

    pages, offset = [], 0
    while True:
        resp = requests.get(
            API_URL,
            params={
                "$select": ",".join(FIELDS),
                "$order": "permitnum",
                "$limit": PAGE_SIZE,
                "$offset": offset,
            },
            headers=headers,
            timeout=60,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        pages.append(pd.DataFrame(batch))
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    df = pd.concat(pages, ignore_index=True).rename(columns=FIELDS)
    # Socrata omits fields that are null in every returned record
    return df.reindex(columns=list(FIELDS.values()))


@st.cache_data(ttl=24 * 3600, show_spinner="Fetching latest permit data...")
def load_data() -> tuple[pd.DataFrame, str]:
    try:
        df = fetch_from_api()
        source = "Live API"
    except Exception:
        if not os.path.exists(LOCAL_CSV):
            raise
        df = pd.read_csv(LOCAL_CSV, low_memory=False, usecols=list(FIELDS.values()))
        source = "Local CSV (API unavailable)"

    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["IssuedDate"] = pd.to_datetime(df["IssuedDate"], errors="coerce")
    df = df.dropna(subset=["IssuedDate"]).copy()
    df["Year"] = df["IssuedDate"].dt.year
    df["Month"] = df["IssuedDate"].dt.to_period("M").dt.to_timestamp()
    df["PermitClassMapped"] = df["PermitClassMapped"].fillna("Unknown")
    return df, source


df, data_source = load_data()
st.caption(
    f"Source: {data_source} · Latest permit issued "
    f"{df['IssuedDate'].max():%b %d, %Y} · {len(df):,} permits"
)

# ------------------------------------------------
# Sidebar Filters
# ------------------------------------------------
st.sidebar.header("Filters")

# A handful of stray permits date back to 1986; almost all data is 2004+.
year_min, year_max = int(df["Year"].min()), int(df["Year"].max())
year_range = st.sidebar.slider(
    "Year Range",
    min_value=year_min,
    max_value=year_max,
    value=(max(2015, year_min), min(2024, year_max)),
)

permit_classes = st.sidebar.multiselect(
    "Permit Class",
    options=sorted(df["PermitClassMapped"].unique()),
    default=sorted(df["PermitClassMapped"].unique()),
)

permit_types = st.sidebar.multiselect(
    "Permit Type",
    options=sorted(df["PermitTypeMapped"].unique()),
    default=sorted(df["PermitTypeMapped"].unique()),
)

statuses = st.sidebar.multiselect(
    "Permit Status (empty = all)",
    options=df["StatusCurrent"].value_counts().index.tolist(),
    default=[],
)

# ------------------------------------------------
# Apply Filters
# ------------------------------------------------
mask = (
    df["Year"].between(*year_range)
    & df["PermitClassMapped"].isin(permit_classes)
    & df["PermitTypeMapped"].isin(permit_types)
)
if statuses:
    mask &= df["StatusCurrent"].isin(statuses)

filtered = df[mask]

if filtered.empty:
    st.warning("No permits match the current filters. Try widening them.")
    st.stop()

# ------------------------------------------------
# KPI Cards
# ------------------------------------------------
permits_per_year = (
    filtered.groupby("Year").size().rename("Permits").reset_index()
)
highest = permits_per_year.loc[permits_per_year["Permits"].idxmax()]

col1, col2, col3, col4 = st.columns(4)
col1.metric("📄 Total Permits", f"{len(filtered):,}", **_METRIC_KW)
col2.metric(
    "📊 Average Per Year",
    f"{int(permits_per_year['Permits'].mean()):,}",
    **_METRIC_KW,
)
col3.metric(
    "🏆 Busiest Year",
    int(highest["Year"]),
    f"{highest['Permits']:,} permits",
    **_METRIC_KW,
)
col4.metric(
    "💰 Median Project Cost",
    f"${filtered['EstProjectCost'].median():,.0f}"
    if filtered["EstProjectCost"].notna().any()
    else "N/A",
    **_METRIC_KW,
)

st.caption(
    f"Showing **{year_range[0]}–{year_range[1]}** · "
    f"{len(filtered):,} of {len(df):,} permits"
)
st.markdown("---")

# ------------------------------------------------
# Tabs
# ------------------------------------------------
tab_trends, tab_breakdown, tab_housing, tab_map, tab_data = st.tabs(
    ["📈 Trends", "🧩 Breakdown", "🏠 Housing", "🗺️ Map", "📋 Data"]
)

with tab_trends:
    # Auto-computed takeaway: compare the two most recent complete years
    current_year = pd.Timestamp.now().year
    complete = permits_per_year[permits_per_year["Year"] < current_year]
    if len(complete) >= 2:
        prev, last = complete.iloc[-2], complete.iloc[-1]
        change = (last["Permits"] - prev["Permits"]) / prev["Permits"] * 100
        direction = "up" if change >= 0 else "down"
        st.info(
            f"**Takeaway:** Permit volume in {int(last['Year'])} was "
            f"**{direction} {abs(change):.1f}%** vs {int(prev['Year'])} "
            f"({last['Permits']:,} vs {prev['Permits']:,} permits)."
        )

    fig = px.bar(
        permits_per_year,
        x="Year",
        y="Permits",
        title="Permits Issued Per Year",
        text_auto=True,
    )
    fig.update_layout(hovermode="x unified", height=450)
    st.plotly_chart(fig, **_STRETCH)

    monthly = filtered.groupby("Month").size().rename("Permits").reset_index()
    fig = px.line(
        monthly,
        x="Month",
        y="Permits",
        title="Monthly Permit Volume",
    )
    fig.update_layout(hovermode="x unified", height=400)
    st.plotly_chart(fig, **_STRETCH)

with tab_breakdown:
    left, right = st.columns(2)

    by_type = (
        filtered.groupby(["Year", "PermitTypeMapped"])
        .size()
        .rename("Permits")
        .reset_index()
    )
    fig = px.bar(
        by_type,
        x="Year",
        y="Permits",
        color="PermitTypeMapped",
        title="Permits by Type",
        labels={"PermitTypeMapped": "Type"},
    )
    fig.update_layout(height=450, legend_orientation="h", legend_y=-0.2)
    left.plotly_chart(fig, **_STRETCH)

    by_class = (
        filtered.groupby(["Year", "PermitClassMapped"])
        .size()
        .rename("Permits")
        .reset_index()
    )
    fig = px.bar(
        by_class,
        x="Year",
        y="Permits",
        color="PermitClassMapped",
        title="Residential vs Non-Residential",
        labels={"PermitClassMapped": "Class"},
    )
    fig.update_layout(height=450, legend_orientation="h", legend_y=-0.2)
    right.plotly_chart(fig, **_STRETCH)

    # Median cost per year (median resists the huge outliers in this column)
    cost = (
        filtered.dropna(subset=["EstProjectCost"])
        .groupby("Year")["EstProjectCost"]
        .median()
        .reset_index()
    )
    fig = px.line(
        cost,
        x="Year",
        y="EstProjectCost",
        title="Median Estimated Project Cost Per Year",
        labels={"EstProjectCost": "Median Cost ($)"},
        markers=True,
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, **_STRETCH)

with tab_housing:
    housing = (
        filtered.groupby("Year")[["HousingUnitsAdded", "HousingUnitsRemoved"]]
        .sum()
        .reset_index()
    )
    housing["Net"] = housing["HousingUnitsAdded"] - housing["HousingUnitsRemoved"]

    total_added = int(housing["HousingUnitsAdded"].sum())
    total_removed = int(housing["HousingUnitsRemoved"].sum())
    total_net = total_added - total_removed
    if len(housing) > 0 and total_added > 0:
        peak = housing.loc[housing["Net"].idxmax()]
        st.info(
            f"**Takeaway:** From {year_range[0]} to {year_range[1]}, permits in "
            f"this selection added **{total_added:,}** housing units and removed "
            f"**{total_removed:,}** — a net gain of **{total_net:,}**. The "
            f"strongest year was **{int(peak['Year'])}** "
            f"(+{int(peak['Net']):,} net units)."
        )

    fig = px.bar(
        housing.melt(
            id_vars="Year",
            value_vars=["HousingUnitsAdded", "HousingUnitsRemoved"],
            var_name="Metric",
            value_name="Units",
        ),
        x="Year",
        y="Units",
        color="Metric",
        barmode="group",
        title="Housing Units Added vs Removed",
    )
    fig.update_layout(height=450, legend_orientation="h", legend_y=-0.2)
    st.plotly_chart(fig, **_STRETCH)

    fig = px.line(
        housing,
        x="Year",
        y="Net",
        title="Net Housing Units Per Year",
        markers=True,
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, **_STRETCH)

with tab_map:
    geo = filtered.dropna(subset=["Latitude", "Longitude"])
    max_points = 5000
    if len(geo) > max_points:
        st.caption(
            f"Showing a random sample of {max_points:,} of {len(geo):,} permits."
        )
        geo = geo.sample(max_points, random_state=42)

    if hasattr(px, "scatter_map"):  # Plotly >= 5.24
        fig = px.scatter_map(
            geo,
            lat="Latitude",
            lon="Longitude",
            color="PermitClassMapped",
            hover_name="PermitNum",
            hover_data={
                "OriginalAddress1": True,
                "PermitTypeMapped": True,
                "Year": True,
                "Latitude": False,
                "Longitude": False,
            },
            labels={"PermitClassMapped": "Class"},
            zoom=10,
            height=600,
        )
        fig.update_layout(
            legend={
                "title": "Permit Class",
                "x": 0.01,
                "y": 0.99,
                "bgcolor": "rgba(255, 255, 255, 0.75)",
                "font": {"color": "black"},
            },
            margin={"l": 0, "r": 0, "t": 0, "b": 0},
        )
        st.plotly_chart(fig, **_STRETCH)
    else:  # fallback for older Plotly
        st.map(geo, latitude="Latitude", longitude="Longitude", size=10)

with tab_data:
    table = filtered.drop(columns=["Month", "Latitude", "Longitude"]).copy()
    table["Record"] = (
        "https://services.seattle.gov/portal/customize/LinkToRecord.aspx?altId="
        + table["PermitNum"]
    )

    query = st.text_input(
        "🔍 Search address or description",
        placeholder="e.g. PIKE ST, garage, solar...",
    )
    if query:
        q = query.strip()
        table = table[
            table["OriginalAddress1"].str.contains(q, case=False, na=False)
            | table["Description"].str.contains(q, case=False, na=False)
        ]

    st.caption(f"{len(table):,} permits match your filters.")
    st.dataframe(
        table,
        hide_index=True,
        column_config={
            "EstProjectCost": st.column_config.NumberColumn(
                "Est. Cost", format="$%.0f"
            ),
            "IssuedDate": st.column_config.DateColumn("Issued"),
            "HousingUnitsAdded": st.column_config.NumberColumn("Units +"),
            "HousingUnitsRemoved": st.column_config.NumberColumn("Units −"),
            "Record": st.column_config.LinkColumn(
                "City Record", display_text="Open ↗"
            ),
        },
        **_STRETCH,
    )
    st.download_button(
        "⬇️ Download filtered data as CSV",
        table.to_csv(index=False).encode(),
        file_name="seattle_permits_filtered.csv",
        mime="text/csv",
    )

# ------------------------------------------------
# Footer
# ------------------------------------------------
st.markdown("---")
st.caption(
    "Data: [City of Seattle Open Data Portal – Building Permits]"
    "(https://data.seattle.gov/d/76t5-zqzr) · refreshed every 24h"
)
