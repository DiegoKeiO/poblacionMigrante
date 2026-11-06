import pandas as pd
import numpy as np
import os

CARPETA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
RUTA = os.path.join(CARPETA_SCRIPT, "..", "data") + os.sep

# ---------------------------------------------------------------------------
# POBLACIÓN OBJETIVO (decisión de diseño -> declararla en la tesis)
# 1) Edad: PEA según INEI = 14 años a más, sin tope superior (misma definición
#    del marco teórico). Es un FILTRO (se eliminan registros), NO un recorte de
#    valores. EDAD_MAX = None significa sin tope; ponle un número solo si decides
#    restringir (p. ej. 64) y declararlo como criterio propio.
# 2) Nacionalidad: en ENAHOPV, los registros con P209A == 1 NO tienen año de
#    llegada ni permiso migratorio, y su "nivel educativo en Venezuela" es casi
#    siempre "Sin nivel": no son migrantes (probablemente peruanos del hogar).
#    VERIFICA el código 1 en el diccionario de ENAHOPV. Si confirmas que es
#    "peruana", déjalo en [1]; si no, usa [].
# ---------------------------------------------------------------------------
EDAD_MIN = 14
EDAD_MAX = None
NACIONALIDADES_EXCLUIDAS = [1]

ml_features_sin_target = [
    'sexo', 'edad', 'estado_civil', 'nacionalidad',
    'nivel_educ_venezuela', 'nivel_educ_peru', 'obtuvo_titulo',
    'homologo_titulo_peru', 'anios_escolaridad_venezuela', 'anios_escolaridad_peru',
    'brecha_educativa_anios', 'tipo_permiso_migratorio', 'tiempo_residencia_anios',
]
ml_features = ml_features_sin_target + ['condicion_laboral']

# ---------------------------------------------------------------------------
# PASO 1: Cargar ambas fuentes CRUDAS y unirlas
# ---------------------------------------------------------------------------
df_enahopv_crudo = pd.read_csv(RUTA + "dataset_final_empleabilidad_migrantes.csv")
df_enahopv_ml = df_enahopv_crudo[ml_features].copy()
df_enahopv_ml["fuente"] = "ENAHOPV_2024"

df_enpove_ml = pd.read_csv(RUTA + "dataset_enpove2022_ml_alineado.csv")
# ya viene con 'fuente' = 'ENPOVE_2022' desde el script anterior

assert set(df_enahopv_ml.columns) == set(df_enpove_ml.columns), "Las columnas no coinciden -- revisa antes de continuar"

df_ml = pd.concat([df_enahopv_ml, df_enpove_ml], ignore_index=True)

print("Dimensiones combinadas (crudo, antes de filtrar):", df_ml.shape)
print("\nDistribución cruzada fuente x condicion_laboral:")
print(pd.crosstab(df_ml["fuente"], df_ml["condicion_laboral"]))

# ---------------------------------------------------------------------------
# PASO 1b: Excluir no migrantes (nacionalidad) -- ver nota arriba
# ---------------------------------------------------------------------------
df_ml["nacionalidad"] = pd.to_numeric(df_ml["nacionalidad"], errors="coerce")
excl = df_ml["nacionalidad"].isin(NACIONALIDADES_EXCLUIDAS)
print(f"\nRegistros con nacionalidad en {NACIONALIDADES_EXCLUIDAS} (se ELIMINAN): {int(excl.sum())}")
print(pd.crosstab(df_ml.loc[excl, "fuente"], df_ml.loc[excl, "condicion_laboral"]))
df_ml = df_ml[~excl].copy()

# ---------------------------------------------------------------------------
# PASO 2: Diagnóstico de edad ORIGINAL (antes de cualquier recorte) y filtro
# ---------------------------------------------------------------------------
df_ml["edad"] = pd.to_numeric(df_ml["edad"], errors="coerce")
print("\nEdad original por fuente:")
print(df_ml.groupby("fuente")["edad"].describe())
print("Edad nula:", int(df_ml["edad"].isna().sum()))

fuera = df_ml["edad"].isna() | (df_ml["edad"] < EDAD_MIN)
if EDAD_MAX is not None:
    fuera |= (df_ml["edad"] > EDAD_MAX)
print(f"\nRegistros fuera de edad [{EDAD_MIN}, {EDAD_MAX if EDAD_MAX is not None else 'sin tope'}] (se ELIMINAN, no se recortan): {int(fuera.sum())}")
print("  -- por fuente x condicion_laboral:")
print(pd.crosstab(df_ml.loc[fuera, "fuente"], df_ml.loc[fuera, "condicion_laboral"]))
print("  -- menores de 14 (no pertenecen a la PEA):", int((df_ml["edad"] < 14).sum()))

df_ml = df_ml[~fuera].copy()
print("Dimensiones tras el filtro de edad:", df_ml.shape)

# ---------------------------------------------------------------------------
# PASO 3: Limpieza SIN fuga de información
# - Categóricas: valor constante 'No Especificado' (no aprende nada de los datos).
# - Numéricas: NO se imputan ni se recortan aquí. La mediana (y, si se decide,
#   los límites de winsorización) se calculan SOLO con el conjunto de
#   entrenamiento, dentro del notebook, después de dividir train/val/test.
# ---------------------------------------------------------------------------
num_cols = [
    'edad', 'anios_escolaridad_venezuela', 'anios_escolaridad_peru',
    'brecha_educativa_anios', 'tiempo_residencia_anios'
]
cat_cols = [
    'sexo', 'estado_civil', 'nacionalidad', 'nivel_educ_venezuela',
    'nivel_educ_peru', 'obtuvo_titulo', 'homologo_titulo_peru', 'tipo_permiso_migratorio'
]

for col in num_cols:
    df_ml[col] = pd.to_numeric(df_ml[col], errors="coerce")

print("\nNulos en numéricas (se imputarán con la mediana de TRAIN en el notebook):")
print(df_ml.groupby("fuente")[num_cols].apply(lambda g: g.isna().sum()))
print("\nRangos originales (sin recorte):")
print(df_ml[num_cols].describe().T[["min", "50%", "max"]])

for col in cat_cols:
    df_ml[col] = df_ml[col].replace(r"^\s*$", np.nan, regex=True).fillna('No Especificado')
    df_ml[col] = df_ml[col].astype('category')

df_ml = df_ml.dropna(subset=['condicion_laboral'])
df_ml['condicion_laboral'] = df_ml['condicion_laboral'].astype('category')

# ---------------------------------------------------------------------------
# PASO 4: Verificar esquema y guardar
# ---------------------------------------------------------------------------
esperadas = set(ml_features + ['fuente'])
assert set(df_ml.columns) == esperadas and df_ml.shape[1] == 15, \
    f"Esquema inesperado: {sorted(set(df_ml.columns) ^ esperadas)}"
assert "tiene_carrera_superior" not in df_ml.columns

df_ml.to_csv(RUTA + "dataset_ml_entrenamiento_combinado.csv", index=False)

print(f"\nDimensiones finales: {df_ml.shape}")
print("\nDistribución final de condicion_laboral (combinado):")
print(df_ml["condicion_laboral"].value_counts())
print("\nPor fuente:")
print(pd.crosstab(df_ml["fuente"], df_ml["condicion_laboral"]))
print(df_ml.columns.tolist())   # 13 variables + condicion_laboral + fuente
