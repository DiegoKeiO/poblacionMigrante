import pandas as pd

df_enpove = pd.read_csv("data/ENPOVE2022_V_200-300-400-500-600-700-800.csv", encoding="utf-8-sig", low_memory=False)
print(df_enpove.shape)
print(df_enpove.columns.tolist())

for col in ['P601', 'P603', 'P604', 'P626', 'P627', 'P629', 'P630', 'P612', 'P613']:
    print(f"\n--- {col} ---")
    print(df_enpove[col].value_counts(dropna=False))