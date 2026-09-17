import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer

# 1. Cargar el dataset consolidado original
df_crudo = pd.read_csv("dataset_final_empleabilidad_migrantes.csv")

# 2. Definir features de ML
ml_features = [
    'sexo', 'edad', 'estado_civil', 'nacionalidad',
    'nivel_educ_venezuela', 'nivel_educ_peru', 
    'obtuvo_titulo', 'homologo_titulo_peru', 'tiene_carrera_superior',
    'anios_escolaridad_venezuela', 'anios_escolaridad_peru', 'brecha_educativa_anios',
    'tipo_permiso_migratorio', 'tiempo_residencia_anios',
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
    'brecha_educativa_anios', 'tiempo_residencia_anios'
]

cat_cols = [
    'sexo', 'estado_civil', 'nacionalidad', 'nivel_educ_venezuela', 
    'nivel_educ_peru', 'obtuvo_titulo', 'homologo_titulo_peru', 
    'tiene_carrera_superior', 'tipo_permiso_migratorio'
]

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

# Forzar tipos de datos para SMOTE-NC
for col in cat_cols:
    df_ml[col] = df_ml[col].astype('category')

# Eliminar desempleados irrecuperables y forzar tipo
df_ml = df_ml.dropna(subset=['condicion_laboral'])
df_ml['condicion_laboral'] = df_ml['condicion_laboral'].astype('category')

# 6. Guardar los archivos listos
df_ml.to_csv("dataset_ml_entrenamiento_limpio.csv", index=False)
df_bi.to_csv("dataset_bi_historico.csv", index=False)

print(f"Dimensiones ML post-limpieza: {df_ml.shape}")
print(f"Nulos restantes en ML: {df_ml.isnull().sum().sum()}")