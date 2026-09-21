import pandas as pd
import numpy as np
import os
from sklearn.impute import SimpleImputer

CARPETA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
RUTA = os.path.join(CARPETA_SCRIPT, "..", "data") + os.sep

ml_features_sin_target = [
    'sexo', 'edad', 'estado_civil', 'nacionalidad',
    'nivel_educ_venezuela', 'nivel_educ_peru',
    'obtuvo_titulo', 'homologo_titulo_peru', 'tiene_carrera_superior',
    'anios_escolaridad_venezuela', 'anios_escolaridad_peru', 'brecha_educativa_anios',
    'tipo_permiso_migratorio', 'tiempo_residencia_anios',
]
ml_features = ml_features_sin_target + ['condicion_laboral']

# ---------------------------------------------------------------------------
# PASO 1: Cargar ambas fuentes CRUDAS (antes de imputar/clipear) y unirlas
# ---------------------------------------------------------------------------
df_enahopv_crudo = pd.read_csv(RUTA + "dataset_final_empleabilidad_migrantes.csv")
df_enahopv_ml = df_enahopv_crudo[ml_features].copy()
df_enahopv_ml["fuente"] = "ENAHOPV_2024"

df_enpove_ml = pd.read_csv(RUTA + "dataset_enpove2022_ml_alineado.csv")
# ya viene con 'fuente' = 'ENPOVE_2022' desde el script anterior

assert set(df_enahopv_ml.columns) == set(df_enpove_ml.columns), "Las columnas no coinciden -- revisa antes de continuar"

df_ml = pd.concat([df_enahopv_ml, df_enpove_ml], ignore_index=True)

print("Dimensiones combinadas (crudo, antes de limpiar):", df_ml.shape)
print("\nDistribución por fuente:")
print(df_ml["fuente"].value_counts())
print("\nDistribución cruzada fuente x condicion_laboral:")
print(pd.crosstab(df_ml["fuente"], df_ml["condicion_laboral"]))

# ---------------------------------------------------------------------------
# PASO 2: Limpieza -- MISMO proceso de siempre, pero ahora sobre el
#         combinado, para que mediana/outliers se calculen con toda la data
# ---------------------------------------------------------------------------
num_cols = [
    'edad', 'anios_escolaridad_venezuela', 'anios_escolaridad_peru',
    'brecha_educativa_anios', 'tiempo_residencia_anios'
]
cat_cols = [
    'sexo', 'estado_civil', 'nacionalidad', 'nivel_educ_venezuela',
    'nivel_educ_peru', 'obtuvo_titulo', 'homologo_titulo_peru',
    'tiene_carrera_superior', 'tipo_permiso_migratorio'
]

imputer_num = SimpleImputer(strategy='median')
df_ml[num_cols] = imputer_num.fit_transform(df_ml[num_cols])

for col in cat_cols:
    df_ml[col] = df_ml[col].fillna('No Especificado')

for col in num_cols:
    lower_limit = df_ml[col].quantile(0.01)
    upper_limit = df_ml[col].quantile(0.99)
    df_ml[col] = np.clip(df_ml[col], lower_limit, upper_limit)

for col in cat_cols:
    df_ml[col] = df_ml[col].astype('category')

df_ml = df_ml.dropna(subset=['condicion_laboral'])
df_ml['condicion_laboral'] = df_ml['condicion_laboral'].astype('category')

# ---------------------------------------------------------------------------
# PASO 3: Guardar
# ---------------------------------------------------------------------------
df_ml.to_csv(RUTA + "dataset_ml_entrenamiento_combinado.csv", index=False)

print(f"\nDimensiones finales post-limpieza: {df_ml.shape}")
print(f"Nulos restantes: {df_ml.isnull().sum().sum()}")
print("\nDistribución final de condicion_laboral (combinado):")
print(df_ml["condicion_laboral"].value_counts())