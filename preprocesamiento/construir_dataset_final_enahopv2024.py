"""
Construcción del dataset final de entrenamiento a partir de ENAHOPV 2024.

Módulos usados (descarga en formato CSV desde proyectos.inei.gob.pe/microdatos):
  - ENAHOPV01-2024-200.csv   -> Características de los miembros del hogar (sexo, edad, estado civil)
  - ENAHOPV01A-2024-300.csv  -> Educación (nivel educ. origen/destino, homologación de título)
  - ENAHOPV01A-2024-500.csv  -> Empleo e Ingreso (nacionalidad, ocupación, sector, informalidad)
  - ENAHOPV.01A-2024-1000.csv -> Situación migratoria y necesidades de protección

pip install pandas --break-system-packages
"""

import pandas as pd
import os

CARPETA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
RUTA = os.path.join(CARPETA_SCRIPT, "..", "data") + os.sep # ajusta si tus CSV están en otra carpeta

# ---------------------------------------------------------------------------
# Clave primaria para unir módulos a nivel de persona
# ---------------------------------------------------------------------------
LLAVE = ["CONGLOME", "VIVIENDA", "HOGAR", "CODPERSO"]


def cargar(nombre_archivo):
    df = pd.read_csv(RUTA + nombre_archivo, encoding="latin-1", low_memory=False)
    # Normaliza nombres de columna por si vienen con espacios o mayúsculas distintas
    df.columns = [c.strip().upper() for c in df.columns]
    return df


# ---------------------------------------------------------------------------
# PASO 1: Cargar cada módulo y quedarte solo con las columnas que necesitas
# ---------------------------------------------------------------------------

# --- Módulo 200: Características del hogar ---
df_200 = cargar("Enahopv01-2024-200.csv")
cols_200 = LLAVE + ["P207", "P208A", "P209"]  # sexo, edad, estado civil
df_200 = df_200[cols_200].rename(columns={
    "P207": "sexo",
    "P208A": "edad",
    "P209": "estado_civil",
})

# --- Módulo 300: Educación ---
df_300 = cargar("Enahopv01A-2024-300.csv")
cols_300 = LLAVE + ["P300B", "P301A", "P301C1", "P301D1", "P301A0"]
df_300 = df_300[cols_300].rename(columns={
    "P300B": "nivel_educ_venezuela",
    "P301A": "nivel_educ_peru",
    "P301C1": "obtuvo_titulo",
    "P301D1": "homologo_titulo_peru",
    "P301A0": "tiene_carrera_superior",
})

# --- Módulo 500: Empleo e ingreso ---
df_500 = cargar("Enahopv01a-2024-500.csv")
cols_500 = LLAVE + [
    "P209A",     # nacionalidad
    "P505R4",    # ocupación principal (CNO-2015)
    "P506R4",    # rama de actividad / sector
    "P513A1",    # años en la ocupación actual
    "P513A2",    # meses en la ocupación actual
    "P511A",     # tipo de contrato
    "OCU500",    # indicador de la PEA (ocupado/desocupado/no PEA)
    "OCUPINF",   # formal / informal
]
df_500 = df_500[cols_500].rename(columns={
    "P209A": "nacionalidad",
    "P505R4": "ocupacion_principal",
    "P506R4": "rama_actividad",
    "P513A1": "anios_en_ocupacion_actual",
    "P513A2": "meses_en_ocupacion_actual",
    "P511A": "tipo_contrato",
    "OCU500": "indicador_pea",
    "OCUPINF": "condicion_formalidad",
})

# --- Módulo 1000: Situación migratoria y necesidades de protección ---
df_1000 = cargar("Enahopv01a-2024-1000.csv")
cols_1000 = LLAVE + ["P1002", "P1000_MES", "P1000_ANHO", "P1011_1"]
df_1000 = df_1000[cols_1000].rename(columns={
    "P1002": "tipo_permiso_migratorio",
    "P1000_MES": "mes_llegada_peru",
    "P1000_ANHO": "anio_llegada_peru",
    "P1011_1": "discriminado_centro_trabajo",
})

# ---------------------------------------------------------------------------
# PASO 2: Unir todos los módulos por la clave de persona
# ---------------------------------------------------------------------------
df = (
    df_500
    .merge(df_200, on=LLAVE, how="left")
    .merge(df_300, on=LLAVE, how="left")
    .merge(df_1000, on=LLAVE, how="left")
)

print(f"Total de personas en el dataset unido: {len(df)}")
print(df["nacionalidad"].value_counts(dropna=False))

# ---------------------------------------------------------------------------
# PASO 2.5: Forzar a numérico las columnas que deberían serlo
# ---------------------------------------------------------------------------
# Los CSV de INEI suelen traer celdas vacías o espacios en blanco para los
# "missing values", lo que hace que pandas lea toda la columna como texto
# (object/string) en vez de número. pd.to_numeric(..., errors="coerce")
# convierte lo que sí es numérico y transforma en NaN cualquier cosa que no
# se pueda convertir (en vez de que todo el script se caiga).
COLUMNAS_NUMERICAS = [
    "edad", "anio_llegada_peru", "mes_llegada_peru",
    "anios_en_ocupacion_actual", "meses_en_ocupacion_actual",
    "nivel_educ_venezuela", "nivel_educ_peru",
    "indicador_pea", "condicion_formalidad",
]
for col in COLUMNAS_NUMERICAS:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Revisa qué tan seguido pasó esto -- si el número de NaN es muy alto,
# probablemente hay un código "missing value" especial (como 9999 o 99) que
# el diccionario documenta y que deberías reemplazar por NaN explícitamente
# ANTES de restar, en vez de dejar que arruine el cálculo de la resta.
print("\nValores nulos tras la conversión numérica (revisa si algún % es muy alto):")
print(df[COLUMNAS_NUMERICAS].isna().sum())

print("\nValores únicos de anio_llegada_peru (busca códigos raros tipo 9999):")
print(sorted(df["anio_llegada_peru"].dropna().unique()))

# ---------------------------------------------------------------------------
# PASO 3: Variable derivada - tiempo de residencia en Perú (en años)
# ---------------------------------------------------------------------------
ANIO_ENCUESTA = 2024
df["tiempo_residencia_anios"] = ANIO_ENCUESTA - df["anio_llegada_peru"]

# ---------------------------------------------------------------------------
# PASO 4: Variable derivada - brecha de nivel educativo (Venezuela vs. Perú)
# ---------------------------------------------------------------------------
# OJO: nivel_educ_venezuela y nivel_educ_peru usan escalas de códigos DISTINTAS
# según el diccionario (una va de 1 a 11, la otra de 1 a 13). Antes de restarlas
# directamente, tienes que armar una tabla de equivalencia entre ambas escalas
# (por ejemplo, mapear las dos a una escala común de "años de estudio
# aproximados"). No las uses tal cual sin ese paso, o la comparación no
# tendrá sentido.

# ---------------------------------------------------------------------------
# PASO 5: Construir la variable objetivo (formal / informal / desempleado)
# ---------------------------------------------------------------------------
# IMPORTANTE: el diccionario no lista las categorías exactas de "indicador_pea"
# (OCU500). Antes de continuar, imprime sus valores únicos para descubrir el
# esquema de códigos real que usa el INEI en esta encuesta:

print("\nValores únicos de indicador_pea (revisa esto antes de continuar):")
print(df["indicador_pea"].value_counts(dropna=False))

print("\nValores únicos de condicion_formalidad:")
print(df["condicion_formalidad"].value_counts(dropna=False))


def construir_variable_objetivo(row):
    """
    Esquema oficial de OCU500 (Indicador de la PEA) confirmado con los conteos
    reales de tu ejecución:
      1 = Ocupado
      2 = Desocupado abierto  (busca trabajo activamente)
      3 = Desocupado oculto   (quiere trabajar pero dejó de buscar)
      4 = No PEA              (no busca trabajo: estudiantes, jubilados, etc.)
      0 = No aplica (residual, muy pocos casos)
    """
    if pd.isna(row["indicador_pea"]):
        return None
    if row["indicador_pea"] in (2, 3):
        return "Desempleado"
    if row["indicador_pea"] == 4:
        return "Inactivo"
    if row["indicador_pea"] == 1:
        if row["condicion_formalidad"] == 1:
            return "Empleado_Informal"
        if row["condicion_formalidad"] == 2:
            return "Empleado_Formal"
    return None


df["condicion_laboral"] = df.apply(construir_variable_objetivo, axis=1)

print("\nDistribución completa (incluye Inactivos, antes de decidir si los excluyes):")
print(df["condicion_laboral"].value_counts(dropna=False))

# ---------------------------------------------------------------------------
# DECISIÓN DE DISEÑO: excluir a los "Inactivos" (No PEA) del dataset final.
# Conceptualmente, alguien que no busca trabajo (estudiante a tiempo completo,
# jubilado, ama de casa) no es un caso de "empleabilidad fallida" -- es un
# fenómeno distinto (participación laboral). Si tu planteamiento del problema
# habla de 3 clases (Formal/Informal/Desempleado), lo correcto es filtrarlos.
# Si en algún momento decides sí incluir "Inactivo" como cuarta clase, borra
# o comenta las siguientes 2 líneas.
# ---------------------------------------------------------------------------
df = df[df["condicion_laboral"] != "Inactivo"].copy()

# Descarta también los pocos residuales sin clasificar (indicador_pea == 0
# u otros casos que no cayeron en ninguna categoría de la función anterior).
df = df[df["condicion_laboral"].notna()].copy()

print("\nDistribución final de la variable objetivo (dataset de entrenamiento):")
print(df["condicion_laboral"].value_counts(dropna=False))

# ---------------------------------------------------------------------------
# PASO 6: Armonizar nivel educativo Venezuela vs. Perú a "años de escolaridad"
# ---------------------------------------------------------------------------
# Aproximación estándar en literatura de economía laboral (similar al criterio
# de bases comparativas internacionales tipo Barro-Lee): cada categoría se
# convierte a un número aproximado de años de estudio, en vez de intentar
# igualar categorías que no son equivalentes entre sistemas educativos.
#
# ADVERTENCIA METODOLÓGICA para tu tesis: estos son valores APROXIMADOS,
# basados en la estructura general de cada sistema educativo. Decláralo
# explícitamente como supuesto/limitación en tu capítulo de metodología.

MAPA_ANIOS_VENEZUELA = {
    1: 0,     # Sin nivel
    2: 0,     # Preescolar
    3: 4.5,   # Educación básica incompleta (aprox., punto medio de 1er-9no grado)
    4: 9,     # Educación básica completa (9no grado)
    5: 10,    # Educación media diversificada incompleta
    6: 11,    # Educación media diversificada completa (Bachillerato)
              # -> Confirmado con Tabla de Equivalencias CAB (Convenio Andrés
              #    Bello): Bachillerato venezolano = 11° grado = mismo total
              #    de años que "Secundaria completa" en Perú.
    7: 12.5,  # Técnico Superior incompleta (aprox., respaldo parcial: ASCUN/CINE-UNESCO)
    8: 14,    # Técnico Superior completa (Nivel CINE 5, ~3 años sobre bachillerato)
    9: 13.5,  # Superior universitaria incompleta (aprox.)
    10: 16,   # Superior universitaria completa (Nivel CINE 6, 5 años estándar sobre
              # bachillerato, según tabla ASCUN con base en Ley Orgánica de Educación
              # 2009 de Venezuela; hay carreras más largas no reflejadas aquí)
    11: 18,   # Maestría/Doctorado (aprox., Nivel CINE 7-8 según ASCUN)
}

MAPA_ANIOS_PERU = {
    1: 0,     # Sin nivel
    2: 0,     # Inicial
    3: 3,     # Primaria incompleta
    4: 6,     # Primaria completa
    5: 8.5,   # Secundaria incompleta
    6: 11,    # Secundaria completa
    7: 12.5,  # Superior no universitaria incompleta
    8: 14,    # Superior no universitaria completa (Nivel CINE 5, ASCUN: 3 años)
    9: 13.5,  # Superior universitaria incompleta
    10: 16,   # Superior universitaria completa (Nivel CINE 6, ASCUN con base en Ley
              # N°30220 y R.M. N°178-2018-MINEDU: 5 años estándar sobre bachillerato;
              # excepción: psicología/derecho 6 años, medicina 7 años -- no reflejado
              # aquí, declárese como limitación)
    11: 19,   # Maestría/Doctorado (aprox., Nivel CINE 7-8 según ASCUN)
    # 12 (Básica especial) y 13 (No ha estudiado en Perú) se tratan aparte,
    # ver nota abajo -- NO tienen un equivalente directo en años de estudio.
}

df["anios_escolaridad_venezuela"] = df["nivel_educ_venezuela"].map(MAPA_ANIOS_VENEZUELA)
df["anios_escolaridad_peru"] = df["nivel_educ_peru"].map(MAPA_ANIOS_PERU)

# CASO ESPECIAL: nivel_educ_peru == 13 ("No ha estudiado en el Perú") no
# significa que la persona no tiene educación -- solo que no ha continuado
# estudios formales EN PERÚ. Para estos casos, lo más razonable es asumir
# que su nivel educativo "actual" es el mismo que trajo de Venezuela (no ha
# sumado ni perdido escolaridad), así que la brecha por definición es 0.
mask_no_estudio_peru = df["nivel_educ_peru"] == 13
df.loc[mask_no_estudio_peru, "anios_escolaridad_peru"] = df.loc[
    mask_no_estudio_peru, "anios_escolaridad_venezuela"
]

# CASO ESPECIAL: nivel_educ_peru == 12 ("Básica especial") no es comparable
# en una escala de años -- lo dejamos como NaN explícitamente.
df.loc[df["nivel_educ_peru"] == 12, "anios_escolaridad_peru"] = None

# Variable final: brecha educativa (positivo = perdió escolaridad relativa
# al no poder continuar/validar estudios en Perú; negativo = ganó escolaridad
# adicional en Perú respecto a lo que trajo)
df["brecha_educativa_anios"] = (
    df["anios_escolaridad_venezuela"] - df["anios_escolaridad_peru"]
)

print("\nDistribución de la brecha educativa (años):")
print(df["brecha_educativa_anios"].describe())

# ---------------------------------------------------------------------------
# PASO 7: Agrupar ocupación y rama de actividad + flag de ocupación actual
# ---------------------------------------------------------------------------
# Reducimos cardinalidad: usamos el Gran Grupo (CNO-2015, 1er dígito) y la
# División económica (CIIU, 2 primeros dígitos) en vez del código detallado,
# para evitar categorías con 1-2 observaciones que el modelo memorizaría
# en vez de generalizar.
df["ocupacion_principal"] = df["ocupacion_principal"].astype(str).str.strip()
df["ocupacion_grupo"] = df["ocupacion_principal"].str[0]
df.loc[df["ocupacion_principal"] == "", "ocupacion_grupo"] = None

df["rama_actividad"] = df["rama_actividad"].astype(str).str.strip()
df["rama_division"] = df["rama_actividad"].str.zfill(4).str[:2]
df.loc[df["rama_actividad"] == "", "rama_division"] = None

print("\nCategorías agrupadas -- ocupación:", df["ocupacion_grupo"].nunique(),
      " | rama:", df["rama_division"].nunique())

# Flag de ocupación actual + imputación de antigüedad para Desempleados
# (para ellos, "0 años/meses en ocupación actual" es correcto: no tienen una)
df["tiene_ocupacion_actual"] = df["anios_en_ocupacion_actual"].notna().astype(int)
df["anios_en_ocupacion_actual"] = df["anios_en_ocupacion_actual"].fillna(0)
df["meses_en_ocupacion_actual"] = df["meses_en_ocupacion_actual"].fillna(0)

# ---------------------------------------------------------------------------
# PASO 8: Guardar el dataset final
# ---------------------------------------------------------------------------
df.to_csv(RUTA + "dataset_final_empleabilidad_migrantes.csv", index=False)
print("\nGuardado como dataset_final_empleabilidad_migrantes.csv")
