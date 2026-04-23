# Backend Ecommerce
## Integrantes

1. Aracely Chavez Ascona <aracely.chavez@utec.edu.pe>
2. Christopher Mendoza Yataco <christopher.mendoza@utec.edu.pe>
3. Hans Arthur Mallma Leon <hans.mallma@utec.edu.pe>
4. Johan Agustin Barrera Alderete <johan.barrera@utec.edu.pe>
5. Jonatan Lavado Azabache <jonatan.lavado@utec.edu.pe>

## Descripción
Backend de e-commerce construido con FastAPI, enfocado en el uso y benchmarking de estructuras de datos avanzadas para resolver problemas reales de alto volumen (hasta millones de productos y transacciones).

| Estructura | Uso |
|------------|-----|
| **Trie** | Autocompletado eficiente de productos en tiempo O(m) donde m = longitud del prefijo |
| **Bloom Filter** | Detección de patrones fraudulentos en transacciones mediante similitud de hashes |
| **Count-Min Sketch** | Mantener Top K transacciones en tiempo real|
| **B+ Tree** | Indexación ordenada de productos para rangos y ordenamientos eficientes |
| **Priority Queue** | Encolado por prioridad de órdenes (EXPRESS > STANDARD > SCHEDULED) |
## Instalación
```
pip install -r requirements.txt
```
## Levantar la app
```
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Idealmente el frontend debería llamar a inicializar la data, pero se puede hacer de manera manual haciendo una llamada a este endpoint:
```
GET /init?products=1000000&transactions=10000000
```
## Endpoints Principales

```
/api/search → B+ Tree
/api/autocomplete → Trie 
/api/top-products → Count-Min Sketch
/api/fraud-check → Bloom Filter 
/api/priority-orders → Heap (cola de prioridad)
/api/benchmark → Suite completa de benchmarks
/api/stats → Estadísticas del sistema
```

## Benchmarks

Para reproducir benchmarks:
```
GET /api/benchmark
```
También puedes forzar regeneración:
```
GET /api/benchmark?regenerate=true
```
