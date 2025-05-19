import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

st.title("Seattle Building Permits Analysis")

# Load the dataset
df = pd.read_csv("Building_Permits.csv")

#Convert IssuedDate
df['IssuedDate'] = pd.to_datetime(df['IssuedDate'], errors= 'coerce' )
df = df.dropna(subset=['IssuedDate'])
df['Year'] = df['IssuedDate'].dt.year

# Sidebar filter
year_range = st.slider("Select year range", min_value=int(df['Year'].min()), max_value=int(df['Year'].max()), value=(2015, 2023))
filtered_df = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]

# Permits per year
permits_per_year = filtered_df['Year'].value_counts().sort_index()

st.subheader("Permits Issued Per Year")
fig, ax = plt.subplots(figsize=(10, 5))
sns.barplot(x=permits_per_year.index, y=permits_per_year.values, ax=ax)
plt.xticks(rotation=45)
st.pyplot(fig)

