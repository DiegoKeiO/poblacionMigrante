"""Arma la fila de entrada del modelo en el orden exacto del entrenamiento."""
import pandas as pd

from app.inference.model_loader import ModeloProduccion


def preparar_fila(perfil: dict, modelo: ModeloProduccion) -> pd.DataFrame:
    """perfil: diccionario guardado en perfiles_migrantes.datos_formulario.

    - Categóricas: cadenas EXACTAS del entrenamiento ('1', '10.0', 'No Especificado').
    - Numéricas: float; si falta alguna derivada (p. ej. nivel 99), se imputa con la
      mediana de entrenamiento del config_produccion.json.
    - CatBoost usa categóricas nativas: no se aplica scaler ni one-hot.
    """
    fila = {}
    for col in modelo.columnas:
        valor = perfil.get(col)
        if col in modelo.cat_cols:
            if valor is None:
                raise ValueError(f"Falta la variable categórica '{col}'.")
            fila[col] = str(valor)
        else:
            fila[col] = float(modelo.medianas[col] if valor is None else valor)
    return pd.DataFrame([fila], columns=modelo.columnas)