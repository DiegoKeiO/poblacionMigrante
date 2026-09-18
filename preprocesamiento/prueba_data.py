import pandas as pd

df = pd.read_csv("data/dataset_final_empleabilidad_migrantes.csv")

for var in ["ocupacion_principal", "rama_actividad", "discriminado_centro_trabajo"]:
    print(f"\n{'='*60}\n{var}\n{'='*60}")
    print(pd.crosstab(df[var], df["condicion_laboral"], normalize="index").round(2))

# Para las de antigüedad (numéricas), no aplica crosstab -- revisamos nulos por clase
for var in ["anios_en_ocupacion_actual", "meses_en_ocupacion_actual"]:
    print(f"\n% de nulos de {var} por clase:")
    print(df.groupby("condicion_laboral")[var].apply(lambda x: x.isna().mean() * 100).round(1))