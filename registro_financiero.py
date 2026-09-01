"""Operaciones financieras compartidas por caja, bancos y cobros."""


def registrar_movimiento_bancario(conn, cuenta_destino, monto, concepto, tipo="Depósito", usuario=None):
    """Registra el movimiento y actualiza el saldo dentro de la transacción."""
    cuenta = str(cuenta_destino or "").strip()
    if not cuenta or float(monto or 0) <= 0 or " - " not in cuenta:
        raise ValueError("La cuenta bancaria y el monto son obligatorios.")
    banco, resto = cuenta.split(" - ", 1)
    numero = resto.split(" (", 1)[0].strip()
    banco = banco.strip()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, saldo FROM cuentas_bancarias WHERE banco=? AND numero_cuenta=? AND estado='Activo' FOR UPDATE",
        (banco, numero),
    )
    fila = cur.fetchone()
    if not fila:
        raise ValueError("La cuenta bancaria ya no está activa o no existe.")
    cuenta_id, saldo_anterior = fila[0], float(fila[1] or 0)
    saldo_nuevo = saldo_anterior + float(monto) if tipo in ("Depósito", "Inicial") else saldo_anterior - float(monto)
    if saldo_nuevo < 0:
        raise ValueError("El movimiento dejaría la cuenta bancaria con saldo negativo.")
    cur.execute(
        "UPDATE cuentas_bancarias SET saldo=? WHERE banco=? AND numero_cuenta=? AND estado='Activo'",
        (saldo_nuevo, banco, numero),
    )
    ahora = __import__("datetime").datetime.now()
    cur.execute(
        """INSERT INTO movimientos_bancarios
           (cuenta_id, banco, numero_cuenta, tipo_movimiento, tipo, concepto, monto,
            fecha, hora, usuario, saldo)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cuenta_id, banco, numero, tipo, tipo, concepto[:255], float(monto),
         ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S"), usuario, saldo_nuevo),
    )
    return saldo_nuevo
