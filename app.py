import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.title(" Seattle Building Permits Analysis")

# Load dataset
df = pd.read_csv("Building_Permits.csv")

# Convert date column and extract year
df['IssuedDate'] = pd.to_datetime(df['IssuedDate'], errors='coerce')
df = df.dropna(subset=['IssuedDate'])
df['Year'] = df['IssuedDate'].dt.year

# Sidebar filter for year range
year_range = st.slider( "Select Year Range",
    min_value=int(df['Year'].min()),
    max_value=int(df['Year'].max()),
    value=(2015, 2023)
)

# Filter data by selected year range
filtered_df = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]

# Count permits per year
permits_per_year = filtered_df['Year'].value_counts().sort_index()

# Create and display bar chart
st.subheader("Permits Issued Per Year")
fig, ax = plt.subplots(figsize=(10, 5))
sns.barplot(x=permits_per_year.index, y=permits_per_year.values, ax=ax)
ax.set_xlabel("Year")
ax.set_ylabel("Number of Permits")
plt.xticks(rotation=45)
st.pyplot(fig)

