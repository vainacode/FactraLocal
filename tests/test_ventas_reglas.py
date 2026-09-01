import unittest
from decimal import Decimal

from dominio.ventas.excepciones import PagoInvalidoError, VentaVaciaError
from dominio.ventas.modelos import ItemVenta
from dominio.ventas.reglas import calcular_cambio, total_items


class ReglasVentasTest(unittest.TestCase):
    def test_total_usa_centavos(self):
        items = [ItemVenta(1, "Filtro", 2, Decimal("10.005"))]
        self.assertEqual(total_items(items), Decimal("20.01"))

    def test_cambio(self):
        self.assertEqual(calcular_cambio("Efectivo", "25", Decimal("20")), Decimal("5.00"))

    def test_credito_no_requiere_efectivo(self):
        self.assertEqual(calcular_cambio("Venta a Crédito", None, Decimal("20")), Decimal("0.00"))

    def test_pago_insuficiente(self):
        with self.assertRaises(PagoInvalidoError):
            calcular_cambio("Efectivo", "19", Decimal("20"))

    def test_venta_vacia(self):
        with self.assertRaises(VentaVaciaError):
            total_items([])


if __name__ == "__main__":
    unittest.main()
