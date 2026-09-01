class RepositorioCotizaciones:
    def insertar_linea(self, conn, numero, cliente, item, fecha, hora, cajero, estado):
        conn.execute("INSERT INTO cotizaciones(cotizacion,cliente,producto,precio,cantidad,total,costo,fecha,hora,cajero,estado) VALUES(?,?,?,?,?,?,?,?,?,?,?)", (numero, cliente, item["producto"], item["precio"], item["cantidad"], item["total"], item["costo"], fecha, hora, cajero, estado))

    def obtener(self, conn, numero):
        return conn.execute("SELECT producto,precio,cantidad,total,costo FROM cotizaciones WHERE cotizacion=?", (numero,)).fetchall()

