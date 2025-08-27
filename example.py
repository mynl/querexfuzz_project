import pandas as pd
from pathlib import Path
from querexfuzz import Querexfuzz

# 1. Create a sample DataFrame
data = {
    'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
    'age': [25, 30, 35, 40, 45],
    'city': ['Amsterdam', 'Berlin', 'Copenhagen', 'Berlin', 'Amsterdam'],
    'registered_date': pd.to_datetime(['2025-08-10', '2025-06-15', '2024-01-20', '2025-08-25', '2025-07-30'])
}
df = pd.DataFrame(data)

# 2. Initialize Querexfuzz with your config file
# (Ensure config.yml is in the same directory or provide the correct path)
qflex_engine = Querexfuzz(config_path='config.yaml')

# 3. Attach the .querexfuzz method to your DataFrame
df = qflex_engine.attach_to(df)

# 4. Run queries!
print("--- People from Berlin ---")
print(df.querexfuzz("where city == 'Berlin'"))

print("\n--- Recently registered (last 3 months) ---")
print(df.querexfuzz("recent @m-3"))

print("\n--- Fuzzy search for 'am', sorted by score ---")
print(df.querexfuzz("# am"))

print("\n--- Complex query: top 1 from Berlin older than 35, select name and age ---")
print(df.querexfuzz("top 1 where city == 'Berlin' and age > 35 select name, age"))
