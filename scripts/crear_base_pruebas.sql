-- Ejecutar como administrador de PostgreSQL, fuera de una transaccion.
-- No modifica factra_db ni concede CREATEDB a pos_app.
CREATE DATABASE factra_test OWNER pos_app;

-- Luego, conectado a factra_test con pos_app:
-- psql -U pos_app -d factra_test -f postgresql/esquema.sql
-- La bateria de pruebas exige:
-- POS_ENV=test
-- POS_DB_NAME=factra_test
-- POS_DB_USER=pos_app
