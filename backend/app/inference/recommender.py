"""Motor híbrido de recomendaciones: reglas (catálogo) + clase predicha + prioridad por SHAP.

Réplica de las funciones evaluar_* y generar_recomendaciones del notebook XAI.
Textos y áreas: catalogo_reglas.json. Grupos educativos y límites: etiquetas.json.
"""
from app.inference.model_loader import ModeloProduccion
from app.inference.utils import norm


def _grupo(codigo, tabla: dict) -> int:
    return tabla.get(norm(codigo), 0)


def _permiso(codigo) -> list[str]:
    c = norm(codigo)
    if c in ("9", "6", "7", "8"):
        return ["R1", "R6"]
    if c in ("5", ""):
        return ["R6"]
    if c == "3":
        return ["R5", "R6"]
    if c == "1":
        return ["R4", "R6"]
    if c == "2":
        return ["R3", "R6"]
    if c == "4":
        return ["R6"]
    return []


def _educacion(obtuvo, homologo, nivel_peru, nivel_ven, g_ven: dict, g_per: dict) -> list[str]:
    ids = []
    obtuvo, homologo = norm(obtuvo), norm(homologo)
    gp, gv = _grupo(nivel_peru, g_per), _grupo(nivel_ven, g_ven)
    if obtuvo == "1" and homologo == "2":
        if gp == 2 or gv == 2:
            ids += ["R7", "R9", "R10", "R12", "R14"]
        elif gp == 1 or gv == 1:
            ids += ["R8"]
        ids += ["R11", "R13"]
    elif obtuvo == "2" and (gp >= 1 or gv >= 1):
        ids += ["R15", "R16"]
    elif gp == 0 and gv == 0:
        ids += ["R17"]
    return ids


def _brecha(nivel_ven, nivel_peru, g_ven: dict, g_per: dict) -> list[str]:
    gv, gp = _grupo(nivel_ven, g_ven), _grupo(nivel_peru, g_per)
    if gv == 2 and gp == 0:
        return ["R18", "R20"]
    if gp == 2:
        return ["R21"]
    return []


def _transversales(clase: str) -> list[str]:
    ids = []
    if clase in ("Desempleado", "Empleado_Informal"):
        ids.append("R13")
    if clase == "Desempleado":
        ids.append("R23")
    if clase == "Empleado_Informal":
        ids += ["R22", "R24"]
    return ids


def _ruta_independiente(clase: str) -> list[str]:
    return ["R25", "R26", "R27", "R29"] if clase == "Empleado_Informal" else []


def ids_activados(modelo: ModeloProduccion, perfil: dict, clase: str) -> list[str]:
    g_ven = modelo.etiquetas["grupo_nivel_venezuela"]
    g_per = modelo.etiquetas["grupo_nivel_peru"]
    ids = []
    ids += _permiso(perfil.get("tipo_permiso_migratorio"))
    ids += _educacion(perfil.get("obtuvo_titulo"), perfil.get("homologo_titulo_peru"),
                      perfil.get("nivel_educ_peru"), perfil.get("nivel_educ_venezuela"), g_ven, g_per)
    ids += _brecha(perfil.get("nivel_educ_venezuela"), perfil.get("nivel_educ_peru"), g_ven, g_per)
    ids += _transversales(clase)
    ids += _ruta_independiente(clase)
    return list(dict.fromkeys(ids))  # sin duplicados, conserva el orden


def generar_recomendaciones(modelo: ModeloProduccion, perfil: dict, clase: str, shap_row, cols_modelo: list[str]):
    """Devuelve (recomendaciones ordenadas y truncadas según la clase, areas_recomendadas)."""
    activadas = ids_activados(modelo, perfil, clase)

    prioridad_var = {rid: r["variable_prioridad"] for rid, r in modelo.catalogo.items() if r.get("variable_prioridad")}
    prioridad = {v: abs(float(shap_row[cols_modelo.index(v)])) for v in set(prioridad_var.values()) if v in cols_modelo}

    def peso(rid: str) -> float:
        v = prioridad_var.get(rid)
        return -prioridad.get(v, 0.0) if v else 0.0

    ordenadas = sorted(activadas, key=peso)  # estable: en empate, queda el orden de activación
    limite = modelo.etiquetas["limite_por_clase"][clase]

    recs = [
        {"id": rid, "area_id": modelo.catalogo[rid]["area_id"], "area": modelo.catalogo[rid]["area"],
         "texto": modelo.catalogo[rid]["texto"]}
        for rid in ordenadas[:limite]
    ]
    areas: dict[str, int] = {}
    for r in recs:
        areas[r["area"]] = areas.get(r["area"], 0) + 1
    return recs, areas