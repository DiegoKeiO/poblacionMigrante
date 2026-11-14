"""Crea una institución y un usuario administrador iniciales.

Uso (desde backend/):
    python -m scripts.seed_admin
"""
from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Institucion, Usuario

INSTITUCION = {"nombre": "Institución de prueba", "siglas": "IP", "ruc": "20000000001"}
ADMIN = {
    "nombre_completo": "Administrador Demo",
    "correo": "admin@demo.pe",
    "password": "Admin12345",
}


def main() -> None:
    db = SessionLocal()
    try:
        inst = db.scalar(select(Institucion).where(Institucion.ruc == INSTITUCION["ruc"]))
        if inst is None:
            inst = Institucion(**INSTITUCION)
            db.add(inst)
            db.commit()
            db.refresh(inst)
            print(f"Institución creada: {inst.nombre} ({inst.id})")

        existe = db.scalar(select(Usuario).where(Usuario.correo == ADMIN["correo"]))
        if existe is None:
            db.add(
                Usuario(
                    institucion_id=inst.id,
                    nombre_completo=ADMIN["nombre_completo"],
                    correo=ADMIN["correo"],
                    password_hash=hash_password(ADMIN["password"]),
                    rol="administrador",
                )
            )
            db.commit()
            print(f"Administrador creado: {ADMIN['correo']} / {ADMIN['password']}")
        else:
            print("El administrador ya existía.")
    finally:
        db.close()


if __name__ == "__main__":
    main()