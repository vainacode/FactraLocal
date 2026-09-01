import ecf_integracion
import factrapi_cliente


class ServicioFiscal:
    """Fachada estable sobre la integración fiscal existente."""

    emitir_venta = staticmethod(ecf_integracion.emitir_venta_ecf)
    emitir_nota = staticmethod(ecf_integracion.emitir_nota)
    @staticmethod
    def anular_comprobante(comprobante_id, motivo=None):
        return factrapi_cliente.datos_respuesta(
            factrapi_cliente.anular_comprobante(comprobante_id, motivo)
        )
    reintentar_pendientes = staticmethod(factrapi_cliente.reintentar_comprobantes_pendientes)
    reconciliar_pendientes = staticmethod(factrapi_cliente.reconciliar_comprobantes_pendientes)

    @staticmethod
    def guardar_nota_local(datos):
        import db_conexion
        with db_conexion.connect("database.db") as conn:
            conn.execute("INSERT INTO notas_credito_debito_locales(tipo,factura_afectada,motivo,monto,fecha,hora,cajero) VALUES(?,?,?,?,?,?,?)", datos)
            conn.commit()
