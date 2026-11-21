"""Utilidades de códigos y etiquetas (réplica de _norm y etiqueta del notebook XAI)."""


def norm(v) -> str:
    """Normaliza un código: '13.0' -> '13'; None/NaN/espacios/'No Especificado' -> '' (sin dato)."""
    s = str(v).strip()
    if s in ("", "nan", "None", "No Especificado"):
        return ""
    try:
        f = float(s)
        return str(int(f)) if f == int(f) else str(f)
    except ValueError:
        return s


def etiqueta(etiquetas: dict, col: str, valor) -> str:
    c = norm(valor)
    d = etiquetas.get(col, {})
    if c in d:
        return d[c]
    return "Sin dato / no aplica" if c == "" else f"cód. {c}"