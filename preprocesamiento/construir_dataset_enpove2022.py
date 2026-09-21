import pandas as pd
import numpy as np
import os

CARPETA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
RUTA = os.path.join(CARPETA_SCRIPT, "..", "data") + os.sep

# ---------------------------------------------------------------------------
# Cargar la base integrada de ENPOVE 2022 (Módulo 10)
# ---------------------------------------------------------------------------
df = pd.read_csv(RUTA + "modulo10_base_integrada_enpove2022.csv", encoding="utf-8-sig", low_memory=False)
df.columns = [c.strip() for c in df.columns]  # ojo: NO uses .upper() aquí, la mayoría ya viene en mayúsculas
                                                # y algunas como 'p802a_3_1' son minúsculas a propósito

print("Dimensiones:", df.shape)

# ---------------------------------------------------------------------------
# Forzar a numérico las columnas que vamos a usar para el árbol de decisión PEA
# ---------------------------------------------------------------------------
COLUMNAS_PEA = [
    'P601', 'P603', 'P604',
    'P605_1', 'P605_2', 'P605_3', 'P605_4', 'P605_5', 'P605_6',
    'P605_7', 'P605_8', 'P605_9', 'P605_10', 'P605_11', 'P605_12',
    'P626', 'P627', 'P629', 'P630',
    'P612', 'P613', 'P205_A',
]
for c in COLUMNAS_PEA:
    df[c] = pd.to_numeric(df[c], errors='coerce')

# ---------------------------------------------------------------------------
# Construir condicion_laboral replicando el árbol de decisión PEA (mismo
# criterio OIT/INEI que ya usaste en ENAHOPV vía OCU500/OCUPINF, aquí armado
# a mano a partir de las preguntas crudas)
# ---------------------------------------------------------------------------
def construir_condicion_laboral(row):
    edad = row['P205_A']
    # El módulo de empleo aplica a personas de 5 y más años -- fuera de ese
    # rango, la pregunta ni siquiera se hizo (children menores de 5)
    if pd.isna(edad) or edad < 5:
        return None

    # --- Paso 1: ¿está OCUPADO? ---
    ocupado = (row['P601'] == 1) or (row['P603'] == 1) or (row['P604'] == 1)
    if not ocupado:
        for i in range(1, 13):
            if row.get(f'P605_{i}') == 1:
                ocupado = True
                break

    if ocupado:
        # --- Paso 2: Formal / Informal según si firmó contrato o dio
        #     comprobante de pago (P613) -- USAR SOLO PARA CONSTRUIR EL
        #     TARGET, nunca como feature de entrenamiento, mismo criterio
        #     que aplicamos con OCUPINF y tipo_contrato en ENAHOPV.
        if row['P613'] == 1:
            return "Empleado_Formal"
        elif row['P613'] == 2:
            return "Empleado_Informal"
        else:
            return None  # ocupado pero sin dato de contrato -- caso raro, se descarta

    # --- Paso 3: no ocupado -> Desocupado abierto, oculto, o Inactivo ---
    busco_trabajo = (row['P626'] == 1) or (row['P627'] == 1)
    if busco_trabajo:
        return "Desempleado"  # desocupado abierto

    queria_y_disponible = (row['P629'] == 1) and (row['P630'] == 1)
    if queria_y_disponible:
        return "Desempleado"  # desocupado oculto

    return "Inactivo"


df['condicion_laboral'] = df.apply(construir_condicion_laboral, axis=1)

print("\nDistribución completa (incluye Inactivos, antes de filtrar):")
print(df['condicion_laboral'].value_counts(dropna=False))

# Mismo criterio de exclusión que en ENAHOPV: fuera Inactivos y residuales sin clasificar
df = df[df['condicion_laboral'] != 'Inactivo'].copy()
df = df[df['condicion_laboral'].notna()].copy()

print("\nDistribución final de la variable objetivo (ENPOVE 2022):")
print(df['condicion_laboral'].value_counts(dropna=False))

df.to_csv(RUTA + "dataset_enpove2022_con_target.csv", index=False)
print("\nGuardado como dataset_enpove2022_con_target.csv")