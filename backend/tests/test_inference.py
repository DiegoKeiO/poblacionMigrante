import json
from pathlib import Path

import pytest

from app.inference import predecir
from app.inference.model_loader import ARTIFACTS_ROOT, VERSION_ACTIVA

REFERENCIA = Path(__file__).parent / "casos_referencia.json"
ARTEFACTOS_OK = (ARTIFACTS_ROOT / VERSION_ACTIVA / "calibracion.json").exists()

pytestmark = pytest.mark.skipif(
    not (ARTEFACTOS_OK and REFERENCIA.exists()),
    reason="Faltan artefactos v1 o tests/casos_referencia.json",
)


def _casos():
    return json.loads(REFERENCIA.read_text(encoding="utf-8"))


@pytest.mark.parametrize("caso", _casos() if REFERENCIA.exists() else [])
def test_coincide_con_colab(caso):
    esperado = caso["esperado"]
    out = predecir(caso["perfil"])

    assert out["prediccion"] == esperado["prediccion"]
    for clase, p in esperado["probabilidades"].items():
        assert out["probabilidades"][clase] == pytest.approx(p, abs=1e-3)
    assert out["niveles_riesgo"]["etapa1"]["nivel"] == esperado["niveles"]["e1"]
    assert out["niveles_riesgo"]["etapa2"]["nivel"] == esperado["niveles"]["e2"]
    assert [e["variable"] for e in out["explicacion"]] == esperado["top_variables"]
    assert [r["id"] for r in out["recomendaciones"]] == esperado["reglas"]