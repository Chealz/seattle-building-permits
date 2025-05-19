import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the dataset
df = pd.read_csv("Building_Permits.csv")

# Print column names to check
print(df.columns)

# Convert 'Issued Date' to datetime (adjust the column name if needed)
df['IssuedDate'] = pd.to_datetime(df['IssuedDate'], errors='coerce')
df = df.dropna(subset=['IssuedDate'])
df['Year'] = df['IssuedDate'].dt.year

# Group and count permits by year
permits_per_year = df['Year'].value_counts().sort_index()

# Plot it
plt.figure(figsize=(10, 6))
sns.barplot(x=permits_per_year.index, y=permits_per_year.values)
plt.title("Seattle Building Permits Issued per Year")
plt.xlabel("Year")
plt.ylabel("Number of Permits")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()