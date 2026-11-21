"""Carga única (al arrancar la API) de los artefactos del modelo versionado."""
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import shap
from catboost import CatBoostClassifier

logger = logging.getLogger(__name__)

ARTIFACTS_ROOT = Path(__file__).parent / "artifacts"
VERSION_ACTIVA = "v1"


class PlattCalibrator:
    """p_cal = sigmoide(coef * logit(p) + intercepto). Equivale a CalibradorPlatt del notebook."""

    def __init__(self, coef: float, intercept: float):
        self.coef = float(coef)
        self.intercept = float(intercept)

    def predict(self, p) -> np.ndarray:
        p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
        z = np.log(p / (1 - p))
        return 1.0 / (1.0 + np.exp(-(self.coef * z + self.intercept)))


@dataclass
class ModeloProduccion:
    version_carpeta: str
    config: dict
    e1: CatBoostClassifier
    e2: CatBoostClassifier
    expl1: shap.TreeExplainer
    expl2: shap.TreeExplainer
    cal1: PlattCalibrator
    cal2: PlattCalibrator
    catalogo: dict          # id -> regla
    etiquetas: dict
    columnas: list = field(default_factory=list)
    cat_cols: list = field(default_factory=list)

    @property
    def version(self) -> str:
        return self.config["version"]

    @property
    def peso_formal(self) -> float:
        return float(self.config["peso_formal_etapa2"])

    @property
    def medianas(self) -> dict:
        return self.config["imputacion_numericas"]["medianas"]


def _leer_json(ruta: Path):
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def cargar_modelo(version_carpeta: str = VERSION_ACTIVA, root: Path = ARTIFACTS_ROOT) -> ModeloProduccion:
    d = root / version_carpeta
    config = _leer_json(d / "config_produccion.json")

    e1, e2 = CatBoostClassifier(), CatBoostClassifier()
    e1.load_model(str(d / config["etapa1"]["archivo"]))
    e2.load_model(str(d / config["etapa2"]["archivo"]))

    # Validaciones: fallar al arrancar es mejor que predecir mal en silencio.
    columnas = list(config["columnas_entrada"])
    if list(e1.feature_names_) != columnas or list(e2.feature_names_) != columnas:
        raise RuntimeError(
            "Los modelos .cbm no coinciden con 'columnas_entrada' de config_produccion.json.\n"
            f"  config : {columnas}\n  etapa 1: {list(e1.feature_names_)}\n  etapa 2: {list(e2.feature_names_)}\n"
            "Copia a la carpeta de artefactos los .cbm de la MISMA versión que el config."
        )
    if list(e1.classes_) != config["clases_etapa1"] or list(e2.classes_) != config["clases_etapa2"]:
        raise RuntimeError("Las clases de los modelos no coinciden con las del config_produccion.json.")

    for k in ("etapa1", "etapa2"):
        if config["calibracion"][k]["metodo"] != "Platt":
            raise RuntimeError("Solo se soporta calibración Platt; el config indica otro método.")
    cal = _leer_json(d / "calibracion.json")

    catalogo = {r["id"]: r for r in _leer_json(d / "catalogo_reglas.json")}
    etiquetas = _leer_json(d / "etiquetas.json")

    modelo = ModeloProduccion(
        version_carpeta=version_carpeta,
        config=config,
        e1=e1,
        e2=e2,
        expl1=shap.TreeExplainer(e1),
        expl2=shap.TreeExplainer(e2),
        cal1=PlattCalibrator(cal["etapa1"]["coef"], cal["etapa1"]["intercept"]),
        cal2=PlattCalibrator(cal["etapa2"]["coef"], cal["etapa2"]["intercept"]),
        catalogo=catalogo,
        etiquetas=etiquetas,
        columnas=columnas,
        cat_cols=list(config["cat_cols"]),
    )
    logger.info("Modelo %s (%s) cargado: %d reglas", modelo.version, version_carpeta, len(catalogo))
    return modelo


_instancia: ModeloProduccion | None = None


def get_modelo() -> ModeloProduccion:
    """Devuelve el modelo cargado (lo carga la primera vez)."""
    global _instancia
    if _instancia is None:
        _instancia = cargar_modelo()
    return _instancia