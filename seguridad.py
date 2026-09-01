"""Utilidades de autenticación local para el POS."""
import hashlib
import hmac
import base64
import os
import secrets


PREFIJO = "pbkdf2_sha256$"
ITERACIONES = 310000
PREFIJO_SECRETO = "fernet$"


def validar_password(password):
    """Valida la política mínima para cuentas nuevas o contraseñas cambiadas."""
    valor = str(password or "")
    return len(valor) >= 8 and any(c.isalpha() for c in valor) and any(c.isdigit() for c in valor)


def _fernet():
    """Construye el cifrador desde un secreto que nunca se guarda en la BD."""
    secreto = os.getenv("POS_FACTRAPI_ENCRYPTION_KEY", "")
    if not secreto:
        return None
    try:
        from cryptography.fernet import Fernet
        clave = base64.urlsafe_b64encode(hashlib.sha256(secreto.encode("utf-8")).digest())
        return Fernet(clave)
    except ImportError as error:
        raise RuntimeError("Falta la dependencia cryptography para cifrar secretos.") from error


def cifrar_secreto(valor):
    if not valor:
        return None
    cifrador = _fernet()
    if cifrador is None:
        if os.getenv("POS_ENV", "development").lower() == "production":
            raise RuntimeError("Configure POS_FACTRAPI_ENCRYPTION_KEY en producción.")
        return valor
    return PREFIJO_SECRETO + cifrador.encrypt(valor.encode("utf-8")).decode("ascii")


def descifrar_secreto(valor):
    if not valor:
        return ""
    if not str(valor).startswith(PREFIJO_SECRETO):
        # Compatibilidad temporal con claves antiguas sin cifrar.
        return str(valor)
    cifrador = _fernet()
    if cifrador is None:
        raise RuntimeError("Configure POS_FACTRAPI_ENCRYPTION_KEY para leer la API Key.")
    try:
        return cifrador.decrypt(str(valor)[len(PREFIJO_SECRETO):].encode("ascii")).decode("utf-8")
    except Exception as error:
        raise RuntimeError("No se pudo descifrar la API Key de FactrAPI.") from error


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("ascii"), ITERACIONES
    ).hex()
    return f"{PREFIJO}{ITERACIONES}${salt}${digest}"


def verificar_password(password, almacenada):
    if not almacenada:
        return False, False
    if not str(almacenada).startswith(PREFIJO):
        # Compatibilidad de migración: las contraseñas antiguas se validan
        # una sola vez y el llamador debe reemplazarlas por un hash.
        return hmac.compare_digest(str(almacenada), password), True
    try:
        algoritmo, rondas, salt, esperado = str(almacenada).split("$", 3)
        if algoritmo != "pbkdf2_sha256":
            return False, False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("ascii"), int(rondas)
        ).hex()
        return hmac.compare_digest(digest, esperado), False
    except (TypeError, ValueError):
        return False, False


def registrar_evento(usuario_id, usuario, evento, detalle=""):
    try:
        import db_conexion
        with db_conexion.connect() as conn:
            conn.execute("""
                INSERT INTO auditoria_eventos (usuario_id, usuario, evento, detalle)
                VALUES (?, ?, ?, ?)
            """, (usuario_id, usuario, evento, detalle[:500]))
            conn.commit()
    except Exception:
        # La auditoría no debe ocultar el resultado de la operación principal.
        pass
