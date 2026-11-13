from app.models.institucion import Institucion
from app.models.usuario import Usuario
from app.models.perfil_migrante import PerfilMigrante
from app.models.version_modelo import VersionModelo
from app.models.prediccion import Prediccion
from app.models.catalogo_regla import CatalogoRegla
from app.models.prediccion_recomendacion import PrediccionRecomendacion

__all__ = [
    "Institucion", "Usuario", "PerfilMigrante", "VersionModelo",
    "Prediccion", "CatalogoRegla", "PrediccionRecomendacion",
]