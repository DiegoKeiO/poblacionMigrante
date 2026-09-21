import pandas as pd
import numpy as np
import os

CARPETA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
RUTA = os.path.join(CARPETA_SCRIPT, "..", "data") + os.sep

df = pd.read_csv(RUTA + "dataset_enpove2022_con_target.csv", low_memory=False)

# ---------------------------------------------------------------------------
# PASO 1: Renombrar columnas de perfil al esquema de ENAHOPV 2024
# ---------------------------------------------------------------------------
df = df.rename(columns={
    "P204": "sexo",
    "P205_A": "edad",
    "P206": "estado_civil",
    "P501": "nivel_educ_venezuela",
    "P501B": "nivel_educ_peru_enpove",    # se remapea abajo, no renombrar directo
    "P512": "obtuvo_titulo",
    "P513": "homologo_titulo_peru",
    "P307": "tipo_permiso_migratorio_enpove",  # se remapea abajo
})

# ---------------------------------------------------------------------------
# PASO 2: Forzar a numérico las columnas que vamos a mapear/comparar
# ---------------------------------------------------------------------------
df["P501A"] = pd.to_numeric(df["P501A"], errors="coerce")
df["nivel_educ_venezuela"] = pd.to_numeric(df["nivel_educ_venezuela"], errors="coerce")
df["nivel_educ_peru_enpove"] = pd.to_numeric(df["nivel_educ_peru_enpove"], errors="coerce")
df["tipo_permiso_migratorio_enpove"] = pd.to_numeric(df["tipo_permiso_migratorio_enpove"], errors="coerce")

print("Distribución de P501A (dónde estudió el último nivel):")
print(df["P501A"].value_counts(dropna=False))

# ---------------------------------------------------------------------------
# PASO 3: Mapeo de permiso migratorio (ENPOVE 15 categorías -> ENAHOPV 9)
# ---------------------------------------------------------------------------
MAPA_PERMISO_MIGRATORIO_ENPOVE_A_ENAHOPV = {
    1: 1, 2: 2, 3: 2, 4: 2, 5: 2, 6: 2, 7: 2, 8: 2,
    9: 1, 10: 6, 11: 3, 12: 3, 13: 4, 14: 5, 15: 9,
}
df["tipo_permiso_migratorio"] = df["tipo_permiso_migratorio_enpove"].map(
    MAPA_PERMISO_MIGRATORIO_ENPOVE_A_ENAHOPV
)

# ---------------------------------------------------------------------------
# PASO 4: nivel_educ_venezuela -- imputar "Sin nivel" (1) para quienes
#         estudiaron en Perú (P501A==2) o no tienen nivel (P501A==3),
#         ya que para ellos P501 (Venezuela) viene vacío por diseño del
#         cuestionario, confirmado con el crosstab contra P501A
# ---------------------------------------------------------------------------
mask_sin_educ_venezuela = df["P501A"].isin([2, 3])
df.loc[mask_sin_educ_venezuela & df["nivel_educ_venezuela"].isna(), "nivel_educ_venezuela"] = 1

# ---------------------------------------------------------------------------
# PASO 5: nivel_educ_peru -- mapear P501B (ENPOVE, "Básica especial"=7)
#         a la escala de ENAHOPV ("Básica especial"=12), solo aplica donde
#         P501A==2; para el resto queda NaN aquí y se completa en el PASO 7
# ---------------------------------------------------------------------------
MAPA_NIVEL_EDUC_PERU_ENPOVE_A_ENAHOPV = {
    1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6,
    7: 12,   # Básica especial: código distinto entre encuestas
    8: 7, 9: 8, 10: 9, 11: 10, 12: 11,
}
df["nivel_educ_peru"] = df["nivel_educ_peru_enpove"].map(MAPA_NIVEL_EDUC_PERU_ENPOVE_A_ENAHOPV)

# ---------------------------------------------------------------------------
# PASO 6: anios_escolaridad_venezuela -- se calcula DESPUÉS de la imputación
#         del PASO 4, para que las 237 personas imputadas también obtengan
#         su valor de años de escolaridad (0, por "Sin nivel")
# ---------------------------------------------------------------------------
MAPA_ANIOS_VENEZUELA = {
    1: 0, 2: 0, 3: 4.5, 4: 9, 5: 10, 6: 11, 7: 12.5, 8: 14, 9: 13.5, 10: 16, 11: 18,
}
MAPA_ANIOS_PERU = {
    1: 0, 2: 0, 3: 3, 4: 6, 5: 8.5, 6: 11, 7: 12.5, 8: 14, 9: 13.5, 10: 16, 11: 19,
}
df["anios_escolaridad_venezuela"] = df["nivel_educ_venezuela"].map(MAPA_ANIOS_VENEZUELA)

# ---------------------------------------------------------------------------
# PASO 7: anios_escolaridad_peru -- mapear directo, y para quienes NO
#         estudiaron en Perú (P501A==1 o 3), copiar el valor de Venezuela
#         (mismo criterio que el código 13 en ENAHOPV: su nivel "actual"
#         es el que trajeron, brecha = 0)
# ---------------------------------------------------------------------------
df["anios_escolaridad_peru"] = df["nivel_educ_peru"].map(MAPA_ANIOS_PERU)

mask_no_estudio_en_peru = df["P501A"].isin([1, 3])
df.loc[mask_no_estudio_en_peru, "anios_escolaridad_peru"] = df.loc[
    mask_no_estudio_en_peru, "anios_escolaridad_venezuela"
]

df["brecha_educativa_anios"] = df["anios_escolaridad_venezuela"] - df["anios_escolaridad_peru"]

print("\nNulos finales tras la corrección:")
for col in ["nivel_educ_venezuela", "nivel_educ_peru", "anios_escolaridad_venezuela",
            "anios_escolaridad_peru", "brecha_educativa_anios", "tipo_permiso_migratorio"]:
    print(f"{col}: {df[col].isnull().sum()}")

df.loc[mask_no_estudio_en_peru, "nivel_educ_peru"] = 13

# ---------------------------------------------------------------------------
# PASO 8: Variables sin equivalente directo -- derivarlas con mejor esfuerzo,
#         documentando el supuesto en la tesis
# ---------------------------------------------------------------------------
# nacionalidad: ENPOVE encuesta solo a venezolanos por diseño
df["nacionalidad"] = 2

# tiene_carrera_superior: sin pregunta equivalente exacta en ENPOVE. Proxy:
# si P502 (carrera que estudia/estudió) tiene valor, asumimos que sí.
# LIMITACIÓN A DOCUMENTAR: es una aproximación, no la misma pregunta original.
df["tiene_carrera_superior"] = df["P502"].notna().astype(int)

# tiempo_residencia_anios: mismo criterio que en ENAHOPV, año de referencia 2022
ANIO_ENCUESTA_ENPOVE = 2022
df["tiempo_residencia_anios"] = ANIO_ENCUESTA_ENPOVE - pd.to_numeric(df["P303_ANIO"], errors="coerce")

# ---------------------------------------------------------------------------
# PASO 9: Quedarnos solo con las columnas de perfil + target, marcar el origen
# ---------------------------------------------------------------------------
ml_features = [
    'sexo', 'edad', 'estado_civil', 'nacionalidad',
    'nivel_educ_venezuela', 'nivel_educ_peru',
    'obtuvo_titulo', 'homologo_titulo_peru', 'tiene_carrera_superior',
    'anios_escolaridad_venezuela', 'anios_escolaridad_peru', 'brecha_educativa_anios',
    'tipo_permiso_migratorio', 'tiempo_residencia_anios',
    'condicion_laboral',
]
df_enpove_ml = df[ml_features].copy()
df_enpove_ml['fuente'] = 'ENPOVE_2022'  # para poder filtrar/auditar después si algo sale raro

print("\nDimensiones finales ENPOVE 2022 listo para concatenar:", df_enpove_ml.shape)
print(df_enpove_ml.isnull().sum())

df_enpove_ml.to_csv(RUTA + "dataset_enpove2022_ml_alineado.csv", index=False)
print("\nGuardado como dataset_enpove2022_ml_alineado.csv")