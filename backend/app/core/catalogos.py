"""Valores permitidos de las variables categóricas.

Estos valores son EXACTAMENTE las cadenas que vio el modelo al entrenar en
Colab (el notebook hace df[cat_cols].astype(str)). El modelo NO usa etiquetas de
texto: usa los CÓDIGOS de las encuestas ENAHOPV/ENPOVE. Por eso:

  * 'nivel_educ_venezuela' y 'nivel_educ_peru' se entrenaron como '6.0', '13.0'...
    (con '.0', porque esas columnas eran decimales en el CSV).
  * El resto de códigos se entrenó como '1', '2', ... y, donde la pregunta no
    aplica, 'No Especificado'.

La interfaz muestra ETIQUETAS (texto), pero al modelo se le envía el CÓDIGO.
Etiquetas verificadas con el Diccionario de Datos ENAHOPV 2024 (INEI):
P207, P209, P209A, P300B, P301A, P301C1, P301D1 y P1002.

Las etiquetas de 'tipo_permiso_migratorio' son las de ENAHOPV (P1002). Los registros
de ENPOVE 2022 (P307, 15 categorías) se convirtieron a esa escala con el mapeo de
dataset_limpio_enpove.py, verificado contra el Diccionario de Variables de ENPOVE:
1,9 -> 1 | 2-8 -> 2 | 11,12 -> 3 | 13 -> 4 | 14 -> 5 | 10 -> 6 | 15 -> 9.
Los códigos 7 y 8 (carné y visa vencidos) solo existen en ENAHOPV.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Categorías observadas en el dataset de entrenamiento (11.069 filas)
# ---------------------------------------------------------------------------
CATEGORIAS: dict[str, list[str]] = {
    "sexo": ["1", "2"],
    "estado_civil": ["1", "2", "3", "4", "5", "6"],
    "nacionalidad": ["2", "3", "4"],
    "nivel_educ_venezuela": ["1.0", "2.0", "3.0", "4.0", "5.0", "6.0", "7.0",
                             "8.0", "9.0", "10.0", "11.0", "99.0"],
    "nivel_educ_peru": ["1.0", "3.0", "4.0", "5.0", "6.0", "7.0", "8.0",
                        "9.0", "10.0", "11.0", "13.0", "99.0"],
    "obtuvo_titulo": ["1", "2", "No Especificado"],
    "homologo_titulo_peru": ["1", "2", "No Especificado"],
    "tipo_permiso_migratorio": ["1", "2", "3", "4", "5", "6", "7", "8", "9",
                                "No Especificado"],
}

# ---------------------------------------------------------------------------
# Etiquetas para la interfaz: {campo: {código_modelo: texto}}
# ---------------------------------------------------------------------------
ETIQUETAS: dict[str, dict[str, str]] = {
    # P207
    "sexo": {"1": "Hombre", "2": "Mujer"},
    # P209
    "estado_civil": {"1": "Conviviente", "2": "Casado(a)", "3": "Viudo(a)",
                     "4": "Divorciado(a)", "5": "Separado(a)", "6": "Soltero(a)"},
    # P209A (el código 1 = Peruano(a) se excluyó del dataset: no son migrantes)
    "nacionalidad": {"2": "Venezolano(a)", "3": "Colombiano(a)", "4": "Otro(a)"},
    # P300B (Venezuela) y P301A (Perú)
    "nivel_educ_venezuela": {
        "1.0": "Sin nivel", "2.0": "Preescolar",
        "3.0": "Educación básica incompleta", "4.0": "Educación básica completa",
        "5.0": "Educación media diversificada incompleta", "6.0": "Educación media diversificada completa",
        "7.0": "Técnico superior incompleta", "8.0": "Técnico superior completa",
        "9.0": "Superior universitaria incompleta", "10.0": "Superior universitaria completa",
        "11.0": "Maestría / Doctorado", "99.0": "Sin dato (missing value)",
    },
    "nivel_educ_peru": {
        "1.0": "Sin nivel", "3.0": "Primaria incompleta", "4.0": "Primaria completa",
        "5.0": "Secundaria incompleta", "6.0": "Secundaria completa",
        "7.0": "Superior no universitaria incompleta", "8.0": "Superior no universitaria completa",
        "9.0": "Superior universitaria incompleta", "10.0": "Superior universitaria completa",
        "11.0": "Maestría / Doctorado", "13.0": "No ha estudiado en el Perú",
        "99.0": "Sin dato (missing value)",
    },
    "obtuvo_titulo": {"1": "Sí", "2": "No", "No Especificado": "No aplica"},
    "homologo_titulo_peru": {"1": "Sí", "2": "No", "No Especificado": "No aplica"},
    # P1002 (ENAHOPV). Ver advertencia del docstring sobre ENPOVE.
    "tipo_permiso_migratorio": {
        "1": "Permiso Temporal vigente (CPP/PTP)",
        "2": "Residencia (Carné de extranjería)",
        "3": "Visa vigente (humanitaria, estudiante, trabajo, turista)",
        "4": "DNI",
        "5": "Otro tipo de permiso",
        "6": "Permiso Temporal vencido (CPP/PTP)",
        "7": "Residencia (Carné de extranjería) vencida",
        "8": "Visa vencida",
        "9": "No cuenta con un permiso migratorio",
        "No Especificado": "No especificado",
    },
}

# Códigos válidos para el modelo pero que no conviene ofrecer en el formulario.
NO_OFRECER_EN_UI: dict[str, set[str]] = {
    "nivel_educ_venezuela": {"99.0"},
    "nivel_educ_peru": {"99.0"},
}

# ---------------------------------------------------------------------------
# Años de escolaridad aproximados por nivel (mismos mapas del preprocesamiento)
# ---------------------------------------------------------------------------
MAPA_ANIOS_VENEZUELA: dict[int, float] = {
    1: 0, 2: 0, 3: 4.5, 4: 9, 5: 10, 6: 11, 7: 12.5, 8: 14, 9: 13.5, 10: 16, 11: 18,
}
MAPA_ANIOS_PERU: dict[int, float] = {
    1: 0, 2: 0, 3: 3, 4: 6, 5: 8.5, 6: 11, 7: 12.5, 8: 14, 9: 13.5, 10: 16, 11: 19,
}
NIVEL_PERU_NO_ESTUDIO = 13   # "No ha estudiado en el Perú"

# Variables que la persona llena. Los años de escolaridad y la brecha NO se
# piden: se calculan con derivar_educacion() a partir de los dos niveles.
CAMPOS_REQUERIDOS: list[str] = [
    "sexo", "edad", "estado_civil", "nacionalidad",
    "nivel_educ_venezuela", "nivel_educ_peru",
    "obtuvo_titulo", "homologo_titulo_peru",
    "tipo_permiso_migratorio", "tiempo_residencia_anios",
]

# Columnas derivadas que el modelo también recibe
CAMPOS_DERIVADOS: list[str] = [
    "anios_escolaridad_venezuela", "anios_escolaridad_peru", "brecha_educativa_anios",
]


def codigo_modelo(campo: str, codigo: int | str) -> str:
    """Convierte un código (p. ej. 6) a la cadena exacta del entrenamiento ('6.0' o '6')."""
    if isinstance(codigo, str) and codigo == "No Especificado":
        return codigo
    n = int(float(codigo))
    return f"{float(n)}" if campo in ("nivel_educ_venezuela", "nivel_educ_peru") else str(n)


def derivar_educacion(nivel_ven: str, nivel_peru: str) -> dict[str, float | None]:
    """Reproduce el cálculo del preprocesamiento.

    anios_escolaridad_venezuela = MAPA_ANIOS_VENEZUELA[nivel_ven]
    anios_escolaridad_peru      = MAPA_ANIOS_PERU[nivel_peru]
                                  ... salvo nivel_peru == 13 (no estudió en Perú):
                                  se copia el valor de Venezuela (brecha = 0)
    brecha_educativa_anios      = anios_venezuela - anios_peru

    Devuelve None donde no hay equivalencia (códigos 99 u otros): quien llame
    debe imputar con las medianas de entrenamiento guardadas en
    config_produccion.json -> imputacion_numericas.medianas.
    """
    nv, np_ = int(float(nivel_ven)), int(float(nivel_peru))
    ven = MAPA_ANIOS_VENEZUELA.get(nv)
    if np_ == NIVEL_PERU_NO_ESTUDIO:
        peru = ven
    else:
        peru = MAPA_ANIOS_PERU.get(np_)
    brecha = None if (ven is None or peru is None) else ven - peru
    return {"anios_escolaridad_venezuela": ven,
            "anios_escolaridad_peru": peru,
            "brecha_educativa_anios": brecha}


def aplica_titulo(nivel_ven: str) -> bool:
    """'obtuvo_titulo' solo se responde con nivel_educ_venezuela en 10 u 11 (criterio común:
    ENPOVE solo lo pregunta ahí; en ENAHOPV se igualó en el preprocesamiento).
    En cualquier otro caso el valor entrenado es 'No Especificado'."""
    return int(float(nivel_ven)) in (10, 11)


def aplica_homologacion(obtuvo_titulo: str) -> bool:
    """'homologo_titulo_peru' solo se responde si obtuvo_titulo == '1'; si no, 'No Especificado'."""
    return obtuvo_titulo == "1"

NOMBRES_VARIABLES: dict[str, str] = {
    "sexo": "Sexo",
    "edad": "Edad",
    "estado_civil": "Estado civil",
    "nacionalidad": "Nacionalidad",
    "nivel_educ_venezuela": "Nivel educativo en Venezuela",
    "nivel_educ_peru": "Nivel educativo en el Perú",
    "obtuvo_titulo": "Obtuvo título",
    "homologo_titulo_peru": "Homologó el título en el Perú",
    "anios_escolaridad_venezuela": "Años de escolaridad en Venezuela",
    "anios_escolaridad_peru": "Años de escolaridad en el Perú",
    "brecha_educativa_anios": "Brecha educativa (años)",
    "tipo_permiso_migratorio": "Permiso migratorio",
    "tiempo_residencia_anios": "Tiempo de residencia (años)",
}