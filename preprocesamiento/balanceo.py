import pandas as pd
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTENC

df = pd.read_csv("dataset_ml_entrenamiento_limpio.csv")

X = df.drop(columns=['condicion_laboral'])
y = df['condicion_laboral']

cat_cols = [
    'sexo', 'estado_civil', 'nacionalidad', 'nivel_educ_venezuela', 
    'nivel_educ_peru', 'obtuvo_titulo', 'homologo_titulo_peru', 
    'tiene_carrera_superior', 'tipo_permiso_migratorio'
]

cat_indices = [X.columns.get_loc(col) for col in cat_cols]

print("Distribución ORIGINAL del Target:")
print(y.value_counts())
print("-" * 40)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, 
    test_size=0.20, 
    random_state=42, 
    stratify=y
)

print("Aplicando SMOTE-NC al conjunto de entrenamiento... (Esto puede tardar unos segundos)")
smote_nc = SMOTENC(categorical_features=cat_indices, random_state=42)

X_train_resampled, y_train_resampled = smote_nc.fit_resample(X_train, y_train)

print("-" * 40)
print("Distribución del Target en ENTRENAMIENTO (Post-SMOTE):")
print(y_train_resampled.value_counts())
print("-" * 40)
print("Distribución del Target en PRUEBA (Sin alterar):")
print(y_test.value_counts())