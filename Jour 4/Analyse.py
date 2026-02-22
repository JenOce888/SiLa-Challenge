import os
os.chdir(r"C:\Users\OCEANE\Documents\SiLa Challenge\Jour 4")
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- Settings for neat visuals ---
sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)

# --- Load datasets ---
titanic = pd.read_csv("Titanic-Dataset.csv")
iris = pd.read_csv("iris.data.csv", header=None,
                   names=["sepal_length", "sepal_width", "petal_length", "petal_width", "species"])
amazon = pd.read_csv("bestsellers with categories.csv")
weather = pd.read_csv("combined_output.csv")

# --- Step 2: Add a source column to each dataset ---
titanic["source"] = "titanic"
iris["source"] = "iris"
amazon["source"] = "amazon"
weather["source"] = "weather"

# --- Merge all into one ---
combined = pd.concat([titanic, iris, amazon, weather], ignore_index=True)

# --- Clean missing values with median ---
numeric_cols = combined.select_dtypes(include="number").columns
combined[numeric_cols] = combined[numeric_cols].fillna(combined[numeric_cols].median())

print("Missing values after cleaning:")
print(combined.isnull().sum().sum())

print("Datasets loaded successfully!")

# --- 1. TITANIC: Survival by Gender ---
sns.countplot(data=titanic, x="Survived", hue="Sex", palette="pastel")
plt.title("Titanic - Survival by Gender")
plt.xticks([0, 1], ["Did not survive", "Survived"])
plt.tight_layout()
plt.savefig("titanic_survival.png")
plt.show()

# --- 2. IRIS: Petal Length by Species ---
sns.boxplot(data=iris, x="species", y="petal_length", palette="Set2")
plt.title("Iris - Petal Length by Species")
plt.tight_layout()
plt.savefig("iris_petal.png")
plt.show()

# --- 3. AMAZON: Top 10 Authors ---
top_authors = amazon["Author"].value_counts().head(10)
sns.barplot(x=top_authors.values, y=top_authors.index, palette="Blues_r")
plt.title("Amazon - Top 10 Most Frequent Authors")
plt.xlabel("Number of Books")
plt.tight_layout()
plt.savefig("amazon_authors.png")
plt.show()

# --- 4. WEATHER: Temperature over time ---
weather["date"] = pd.to_datetime(weather["date"], errors="coerce")
weather_clean = weather.dropna(subset=["date"])
sns.lineplot(data=weather_clean, x="date", y="temp_max", color="coral", label="Max Temp")
sns.lineplot(data=weather_clean, x="date", y="temp_min", color="steelblue", label="Min Temp")
plt.title("Weather - Temperature Over Time (2018-2022)")
plt.tight_layout()
plt.savefig("weather_temp.png")
plt.show()

# --- Step 3: Detect outliers with IQR ---
print("\nOutliers detected per column:")
for col in numeric_cols:
    Q1 = combined[col].quantile(0.25)
    Q3 = combined[col].quantile(0.75)
    IQR = Q3 - Q1
    outliers = combined[(combined[col] < Q1 - 1.5 * IQR) | (combined[col] > Q3 + 1.5 * IQR)]
    print(f"{col}: {len(outliers)} outliers")

# --- Step 4: Create derived features ---
combined["mean_numeric"] = combined[numeric_cols].mean(axis=1)
combined["median_numeric"] = combined[numeric_cols].median(axis=1)
combined["std_numeric"] = combined[numeric_cols].std(axis=1)

print("\nNew features added:")
print(combined[["mean_numeric", "median_numeric", "std_numeric"]].head())

# --- Step 5: Export to CSV and Excel ---
combined.to_csv("final_output.csv", index=False)

print("\nFiles exported successfully!")
print(f"Total rows: {len(combined)}")
print(f"Total columns: {len(combined.columns)}")
