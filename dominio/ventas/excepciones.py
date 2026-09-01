class ErrorNegocio(Exception):
    """Base para errores esperables del flujo comercial."""


class CajaCerradaError(ErrorNegocio):
    pass


class VentaVaciaError(ErrorNegocio):
    pass


class StockInsuficienteError(ErrorNegocio):
    pass


class PagoInvalidoError(ErrorNegocio):
    pass


class TotalInvalidoError(ErrorNegocio):
    pass

