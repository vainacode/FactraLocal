class CajaError(Exception):
    pass


class CajaNoAbiertaError(CajaError):
    pass


class MontoInvalidoError(CajaError):
    pass

