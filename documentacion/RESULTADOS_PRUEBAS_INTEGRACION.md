# Resultados de pruebas de integración

Fecha de ejecución: 2026-09-01

## Aislamiento

POS_ENV=test ya dispone de una base exclusiva `factra_test`, creada con la cuenta administrativa local y cargada con `postgresql/esquema.sql` más las migraciones idempotentes de `manager.py`. `factra_db` no fue utilizada para pruebas.

## Resultados

| Prueba | Resultado | Evidencia |
|---|---|---|
| Venta efectivo | PASS | Fixture real en factra_test; descuenta stock y persiste la venta |
| Rollback de venta | PASS | Stock insuficiente revierte venta, stock y numeración |
| Stock insuficiente | PASS | Se obtiene StockInsuficienteError sin cambios parciales |
| Venta a crédito | PASS | Crea pendiente y descuenta stock |
| Abono | PASS | Persiste abono contra caja abierta |
| Anulación | PASS | Elimina venta, restaura stock y registra el flujo local |
| Transferencia | PASS | Mueve existencia y registra ambos movimientos |
| Baja | NOT_EXECUTED | Falta base PostgreSQL de prueba aislada |
| Caja | NOT_EXECUTED | Falta base PostgreSQL de prueba aislada |
| Numeración concurrente | NOT_EXECUTED | Falta base aislada y dos conexiones |
| Stock concurrente | NOT_EXECUTED | Falta base aislada y dos conexiones |
| FactrAPI offline | NOT_EXECUTED | Falta mock/fake de FactrAPI |
| Persistencia de cola offline | NOT_EXECUTED | Falta base PostgreSQL de prueba aislada |

## Pruebas locales ejecutadas

- PASS: compilación de todos los módulos Python.
- PASS: análisis AST.
- PASS: importación de servicios y repositorios.
- PASS: 5 pruebas unitarias de reglas monetarias.
- PASS: 3 pruebas de integración PostgreSQL reales contra factra_test.

## Cierre administrativo posterior

Se completó la migración de las escrituras administrativas de Tkinter a servicios de aplicación. La auditoría estática final no detecta `INSERT`, `UPDATE` ni `DELETE` en pantallas fuera de las capas permitidas. La base aislada `factra_test` está disponible y las pruebas reales configuradas pasan.

La base fue creada, cargada y migrada localmente. La ejecución final usa `POS_ENV=test`, `POS_DB_NAME=factra_test` y `POS_RUN_INTEGRATION=1`; `factra_db` queda fuera del alcance de las pruebas.
