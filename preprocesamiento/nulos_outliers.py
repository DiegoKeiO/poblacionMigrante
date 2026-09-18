import pandas as pd
import numpy as np
import os
from sklearn.impute import SimpleImputer


CARPETA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
RUTA = os.path.join(CARPETA_SCRIPT, "..", "data") + os.sep

# 1. Cargar el dataset consolidado original
df_crudo = pd.read_csv(RUTA + "dataset_final_empleabilidad_migrantes.csv")

# 2. Definir features de ML
ml_features = [
    'sexo', 'edad', 'estado_civil', 'nacionalidad',
    'nivel_educ_venezuela', 'nivel_educ_peru', 
    'obtuvo_titulo', 'homologo_titulo_peru', 'tiene_carrera_superior',
    'anios_escolaridad_venezuela', 'anios_escolaridad_peru', 'brecha_educativa_anios',
    'tipo_permiso_migratorio', 'tiempo_residencia_anios',
    'ocupacion_grupo', 'rama_division',                                    # <-- NUEVO
    'tiene_ocupacion_actual', 'anios_en_ocupacion_actual', 'meses_en_ocupacion_actual',  # <-- NUEVO
    'condicion_laboral' # Target
]

# 3. Separar los datasets: ML y Business Intelligence (BI)
df_ml = df_crudo[ml_features].copy()

bi_features = ml_features + [
    'CONGLOME', 'VIVIENDA', 'HOGAR', 'CODPERSO', 
    'ocupacion_principal', 'rama_actividad', 'tipo_contrato',
    'anios_en_ocupacion_actual', 'meses_en_ocupacion_actual',
    'discriminado_centro_trabajo'
]
df_bi = df_crudo[bi_features].copy()

# 4. Definir columnas numéricas y categóricas para la limpieza
num_cols = [
    'edad', 'anios_escolaridad_venezuela', 'anios_escolaridad_peru', 
    'brecha_educativa_anios', 'tiempo_residencia_anios',
    'anios_en_ocupacion_actual', 'meses_en_ocupacion_actual'   # <-- NUEVO
]

cat_cols = [
    'sexo', 'estado_civil', 'nacionalidad', 'nivel_educ_venezuela', 
    'nivel_educ_peru', 'obtuvo_titulo', 'homologo_titulo_peru', 
    'tiene_carrera_superior', 'tipo_permiso_migratorio',
    'ocupacion_grupo', 'rama_division'    # <-- NUEVO
]

# tiene_ocupacion_actual es un flag binario (0/1), no lo tratamos como numérica
# continua para imputación/outliers -- lo dejamos fuera de num_cols y lo agregamos
# directo al df_ml sin pasar por SimpleImputer ni clipping de cuantiles
flag_cols = ['tiene_ocupacion_actual']   # <-- NUEVO

# 5. Limpieza y formateo sobre df_ml
# Imputación de numéricas con mediana
imputer_num = SimpleImputer(strategy='median')
df_ml[num_cols] = imputer_num.fit_transform(df_ml[num_cols])

# Imputación de categóricas con valor constante
for col in cat_cols:
    df_ml[col] = df_ml[col].fillna('No Especificado')

# Tratamiento de Outliers
for col in num_cols:
    lower_limit = df_ml[col].quantile(0.01)
    upper_limit = df_ml[col].quantile(0.99)
    df_ml[col] = np.clip(df_ml[col], lower_limit, upper_limit)

# El flag binario se queda tal cual (0/1), sin imputar ni recortar
df_ml[flag_cols] = df_ml[flag_cols].fillna(0).astype(int)   # <-- NUEVO

# Forzar tipos de datos para SMOTE-NC
for col in cat_cols:
    df_ml[col] = df_ml[col].astype('category')

# Eliminar registros sin condicion_laboral y forzar tipo
df_ml = df_ml.dropna(subset=['condicion_laboral'])
df_ml['condicion_laboral'] = df_ml['condicion_laboral'].astype('category')

# 6. Guardar los archivos listos
df_ml.to_csv(RUTA + "dataset_ml_entrenamiento_limpio.csv", index=False)
df_bi.to_csv(RUTA + "dataset_bi_historico.csv", index=False)

print(f"Dimensiones ML post-limpieza: {df_ml.shape}")
print(f"Nulos restantes en ML: {df_ml.isnull().sum().sum()}")
print(f"\nDistribución tiene_ocupacion_actual por clase:")
print(df_ml.groupby('condicion_laboral')['tiene_ocupacion_actual'].value_counts())