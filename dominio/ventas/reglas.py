from decimal import Decimal, ROUND_HALF_UP

from .excepciones import PagoInvalidoError, TotalInvalidoError, VentaVaciaError
from .modelos import ItemVenta


CENTAVOS = Decimal("0.01")


def dinero(valor) -> Decimal:
    return Decimal(str(valor or 0)).quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def total_items(items: list[ItemVenta]) -> Decimal:
    if not items:
        raise VentaVaciaError("No hay productos en la venta.")
    total = sum((item.total for item in items), Decimal("0"))
    total = total.quantize(CENTAVOS, rounding=ROUND_HALF_UP)
    if total <= 0:
        raise TotalInvalidoError("El total de la venta debe ser mayor que cero.")
    return total


def validar_pago(medio_pago: str, cuenta_destino: str | None) -> None:
    if medio_pago not in ("Efectivo", "Venta a Crédito") and not cuenta_destino:
        raise PagoInvalidoError("Seleccione la cuenta bancaria utilizada para el pago electrónico.")


def calcular_cambio(medio_pago: str, monto_recibido, total: Decimal) -> Decimal:
    if medio_pago == "Venta a Crédito":
        return Decimal("0.00")
    recibido = dinero(monto_recibido)
    if recibido < total:
        raise PagoInvalidoError("El monto recibido es menor al total de la venta.")
    return (recibido - total).quantize(CENTAVOS, rounding=ROUND_HALF_UP)
