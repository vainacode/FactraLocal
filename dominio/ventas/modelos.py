from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional


@dataclass(frozen=True)
class ItemVenta:
    producto_id: int
    producto: str
    cantidad: int
    precio: Decimal
    costo: Decimal = Decimal("0")

    @property
    def total(self) -> Decimal:
        return (self.precio * self.cantidad).quantize(Decimal("0.01"))


@dataclass(frozen=True)
class SolicitudVenta:
    cliente: str
    items: list[ItemVenta]
    medio_pago: str
    usuario: str
    caja_id: int
    almacen_id: Optional[int]
    cuenta_destino: Optional[str] = None
    total: Optional[Decimal] = None
    monto_recibido: Optional[Decimal] = None
    factura_pendiente_retomada: Optional[int] = None


@dataclass(frozen=True)
class ResultadoVenta:
    numero_factura: int
    total: Decimal
    cambio: Decimal
    ncf_tradicional: Optional[str] = None
    ncf_electronico: Optional[str] = None
    estado_fiscal: Optional[str] = None
    comprobante_id: Optional[Any] = None
    fiscal_pendiente: bool = False
    motivo_fiscal: Optional[str] = None


@dataclass(frozen=True)
class ResultadoPendiente:
    numero_factura: int
    total: Decimal
