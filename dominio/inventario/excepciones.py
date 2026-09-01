class InventarioError(Exception):
    pass


class StockInsuficienteError(InventarioError):
    pass


class AlmacenesInvalidosError(InventarioError):
    pass

