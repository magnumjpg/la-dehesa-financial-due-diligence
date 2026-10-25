# Gobernanza del modelo financiero — La Dehesa del Castrillo S.L.

**Documento de gobernanza · octubre de 2026 · esquema de auditoría 4.0.0**

## 1. Propósito y estado

Este documento fija cómo se construye, controla y cambia el modelo financiero de La Dehesa del Castrillo S.L. Su ámbito es el repositorio Python + Excel, no la decisión de inversión; no sustituye una auditoría independiente, una tasación ni un term sheet.

El estado es **reproducible y auditado**, sin revisión de terceros. La auditoría evalúa 16 reglas: 10 pasan, 5 excepciones materiales y 1 warning. El veredicto es `CONDITIONAL - 5 MATERIAL EXCEPTION(S)`; la recomendación es `DECLINE AS STRUCTURED (RESIZE REQUIRED)`. R7 supera el WACC y el test neto con un gap del 3,2%, solo a 110 k€ por cabaña; procede un test de Fase 0, no construir.

## 2. Mapa del modelo

| Archivo | Responsabilidad |
|---|---|
| `main.py` | Pipeline de 15 pasos: casos, funding, deuda, retornos, reforma, auditoría y entregables. |
| `statements.py`, `debt.py`, `tax.py` | Tres estados, deuda francesa, IVA, Sociedades y BIN. |
| `reform.py` (core y config) | R1-R7, presets, value bridge, frontera, stress, valoración y distress. |
| `assumptions.py` | CapEx, deuda, personal, OPEX, economía unitaria y escenarios. |
| `model_audit.py` | 16 reglas calculadas y JSON de auditoría. |
| `funding.py`, `metrics.py`, `expansion.py`, `monthly_cash.py` | Fuentes y usos, DSCR/TIR/VAN, gate de Fase II y liquidez mensual. |
| `export_excel.py`, `live_excel.py` | Libro de 13 pestañas y 2.060 fórmulas. |
| `tests/`, `data/*.json`, `data/*.xlsx` | 73 tests y salidas; el Excel y los JSON no son fuente de verdad. |

## 3. Flujo de cálculo

Secuencia: as-is → funding → deuda → retornos → reforma R1-R6 → R7 → auditoría.

### 3.1 As-is

| Caso | Ingresos A1 | EBITDA A1 | DSCR mínimo |
|---|---:|---:|---:|
| Gestión | 154.548,00 € | 24.279,92 € | 1,15x |
| Mercado INE | 95.555,00 € | -18.565,58 € | -1,46x |
| Promotor (re-modelado) | 86.275,00 € | 11.297,00 € | 0,33x |

CapEx: 1.050.100 €; equity en caja: 521.090,22 € (49,62%). Gestión es upside; mercado usa el INE 21,24%; el promotor se re-modela sobre las cifras de titular de la presentación (86.275 € / 11.297 €), no es una réplica de los libros fuente: la §2 del README concilia las cuatro cifras de ingresos que contienen.

### 3.2 Funding

Usos: 1.306.646,22 € (CapEx en caja 800.100, IDC 14.701,40, IVA 168.021, preapertura 35.000, capital circulante 25.000, DSRA 13.823,82). Fuentes: deuda 367.535, puente de IVA 168.021, equity 521.090,22 y terreno 250.000. Gap: 0,00 €. El equity es un plug, no un supuesto.

### 3.3 Deuda

Francesa a 20 años, 4,0% fijo, 12 meses de construcción con IDC y 12 de carencia. Servicio desde el Año 2: 27.647,64 €; cierre en el mes 240. Se dimensiona sobre el mínimo CFADS pre-impuestos de los años 2+, con 1,25x DSCR y tope 35% LTV. El DSCR manda: tope de 339.144,92 € frente a 367.535 € solicitados.

### 3.4 Retornos

Salida base: EBITDA del Año 5 / 8,5%, sin costes de venta. TIR de proyecto de gestión: -9,49% frente a WACC del 8%; valor terminal: 435.783 €. El promotor es el único con TIR positiva, pero no supera el WACC.

### 3.5 Reforma R1-R6

R2 añade seis cubiertos externos al día, +5% de ADR, experiencias, 5.000 € de ahorros y un FTE: EBITDA maduro 71.321 €, DSCR 2,13x y gap neto de -324.723 €. R1, R3 y R5 mejoran el VAN sin cerrar el hueco; R4 solo pasa en el rincón agresivo; R6 tiene EBITDA negativo y valor cero.

### 3.6 R7: cabañas premium

| Caso | Configuración | CapEx | EBITDA A5 | DSCR mín. | Gap neto | TIR |
|---|---|---:|---:|---:|---:|---:|
| Base | 6 cabañas + casa, ADR 200 €, 50%, 110 k€/cabaña | 1.441.600 € | 155.712,50 € | 1,41x | +49.146,54 € | 9,21% |
| Stretch | 6 × 150 k€, ADR 230 €, 55% | 1.708.000 € | — | 3,30x | +506.865 € | 14,33% |
| Downside | 5 cabañas, ADR 190 €, 45%, 150 k€/cabaña | 1.541.500 € | 71.597,62 € | 0,79x | -988.767 € | -9,23% |

Inversión total base: 1.540.760,04 €; VAN: +76.416,23 €. Escalera: 110 k€ +49.147 €; 120 k€ -19.263 €; 130 k€ -87.672 €; 150 k€ -224.490 €; 180 k€ -429.718 €. Valoración: yield on cost 10,11%, cap 9,50%, equilibrio 9,80% (30,3 pb); sin compresión, -46.222,80 €; EBITDA de equilibrio neto 150.899,18 € (margen 4.813,32 €); múltiplo 10,53x; a 9x/10,5x/12x, -181.390/+45.172/+271.733 €.

Downside: DSCR mínimo 0,79x en el Año 1; déficit de CFADS 4.577,04 €; DSRA de seis meses 20.292,72 €, que lo cubre; cure a 1,25x 17.455,75 €. Salida neta 654.606,82 € frente a deuda 457.236,43 €: recuperación del prestamista 143%; equity 197.370,39 € sobre 1.113.342,89 € invertidos (17,7%).

## 4. Convenciones

| Convención | Regla |
|---|---|
| Moneda y unidades | Euros, importes completos. Reforma y R7 en euros constantes de 2026. |
| Precios | Reforma/R7: ADR, OPEX y nómina planos en términos reales; mercado y promotor conservan el nominal heredado. |
| Signos | Ingresos y costes en positivo; los costes se restan. Inversión y amortización, negativas en los flujos. |
| Redondeo | Dos decimales en importes; ratios a dos decimales en presentación. Tolerancia Excel: 1 € / 0,01x. |
| IVA | 10% en alojamiento y restaurante; 21% en CapEx y OPEX. Operativo pass-through; el de CapEx (168.021 €) se financia con puente de 175.000 € y se cobra en el mes 18. Liquidación anual. |
| Proyección | Estados anuales a cinco años; deuda mensual a 240 meses; liquidez mensual a 24 meses, conciliada a 0,00 €. |
| BIN | Sociedades 25% plano, sin régimen de nueva entidad (15%/20%); bases negativas en el horizonte y activo diferido. |
| Deuda | Francesa, 20 años, 12 meses de construcción y 12 de carencia, tipo fijo. Sin cash sweep ni cure. |
| Salida | As-is 8,5% bruto; R7 9,5% de cap. Costes del 3% (4% en R6 y downside R7). Sin tasación independiente. |

La subvención de capital no se imputa a resultados; entra en patrimonio.

## 5. Controles y reconciliación

| Control | Resultado |
|---|---|
| Tests | 68 automatizados tras el último cambio (antes 65). |
| Auditoría | 16 reglas: 10 pasan, 5 fallos materiales y 1 warning. |
| Balance | Discrepancia máxima de 0,00 € en los tres casos (tolerancia 0,01 €). |
| Python ↔ Excel | 13 pestañas y 2.060 fórmulas; DSCR A2 1,1534x y cajas A1/A2 de 20.700,88/183.322,64 €, dentro de 1 € / 0,01x. |
| Puente de valor R2 | Residuo cero entre palancas y EBITDA de la reforma. |
| Determinismo | Pipeline determinista; Monte Carlo y cópulas con semilla 42. |
| Trazabilidad | JSON de auditoría (esquema 4.0.0) y de reforma con presets y stress. |

La auditoría se deja fallar a propósito. Las reglas de integridad —balance, IVA, fuentes y usos, réplica del promotor y FF&E— pasan; los fallos son condiciones económicas, no errores de fórmula. El covenant del Excel muestra `FAIL`, resultado correcto.

## 6. Log de supuestos

| Supuesto | Valor | Base | Fuente o razón | Dónde duele |
|---|---|---|---|---|
| Terreno | 250.000 € | Juicio | Valor de oportunidad en todos los casos | Gap y VAN |
| CapEx base | 1.050.100 € | Medido | Presupuesto técnico | R2, R3 y gap |
| CapEx R7 | 1.441.600 € | Triangulado | 110 k€/cabaña | A 120 k€ falla |
| Inversión total R7 | 1.540.760,04 € | Medido | Suma del motor | Test neto y TIR |
| Ocupación gestión | 31,36% | Juicio | 1,48x INE | RULE_10/05 |
| Ocupación mercado | 21,24% | Medido | INE EOTR 2025 | RULE_14 |
| Rampa mercado | 25%/20% y +5% desde A4 | Juicio | Herencia del Excel | Caso mercado |
| ADR R7 | 200 €; casa 400 € | Triangulado | Banda 180-210 € | Base; stretch 230 € |
| Ocupación R7 | 35%/45%/50% | Juicio | Banda 45-55% | DSCR 1,41x |
| Cabañas | 6 × 110 k€ | Triangulado | Benchmark, no oferta | 120 k€ falla |
| Covers externos | 6/día R2; 10/día R7 | Juicio | Sin competitive set | EBITDA y R7 |
| Experiencias R7 | 45.000 € | Juicio | Sin programa firmado | EBITDA y salida |
| FTE incremental | 1,0 R2; 4,5 R7 | Juicio | Mínimo operativo | Nómina y margen |
| Nómina | 60.075 € + Seguridad Social | Medido | Convenio y SMI 2026 | RULE_04 |
| OPEX fijo | 30.500 € | Triangulado | Schedule USALI | EBITDA |
| Coste variable | 385,25 €/día ocupado | Medido | Stack variable | Margen |
| Reserva FF&E | 3% de ingresos | Juicio | Estándar sectorial | RULE_16 y CFADS |
| Deuda | 35% LTV, 20 años, 4,0%, 12+12 | Triangulado | Términos rurales 2026 | DSCR y equity |
| Objetivo DSCR | 1,25x sobre CFADS pre-tax A2+ | Medido | Covenant | RULE_05 |
| DSRA | 6 meses; 13.823,82 € | Medido | Contractual | RULE_07 |
| LEADER | 163.000 € | Juicio | Sin carta de concesión | R3, R6 y caja |
| Fiscalidad | IVA 10/21; IS 25%; BIN | Medido | Leyes 37/1992 y 27/2014 | RULE_02/03/12 |
| Salida | Cap 9,5%; costes 3% (4% downside) | Juicio | Sin tasación | Gap neto y TIR |
| WACC | 8,0% | Juicio | Hurdle de proyecto | VAN y RULE_12 |

## 7. Disposición de excepciones de auditoría

Ningún fallo es un defecto de fórmula: no hay signos invertidos, dobles cómputos ni referencias rotas. Las excepciones son hallazgos del deal: la estructura o la demanda no cumplen el covenant o el coste de capital.

| Regla | Hallazgo | ¿Defecto de modelo o hallazgo del deal? | Disposición | Condición de cierre |
|---|---|---|---|---|
| RULE_05 | DSCR de gestión 1,15x vs 1,25x | Hallazgo del deal: la deuda al 35% LTV no soporta la amortización | Redimensionar a 339.144,92 € o aportar equity | DSCR ≥ 1,25x y 10% de headroom |
| RULE_11 | Fase II: -252.241,06 €; `DO NOT PROCEED` | Hallazgo del deal: la caja de Fase I no cubre la Fase II | No ejecutar; mantener el gate | Financiación comprometida y aprobación |
| RULE_12 | TIR -9,49% vs WACC 8% | Hallazgo del deal: el activo no gana su coste de capital | Declinar; R7 solo tras Fase 0 | VAN > 0 o terminación |
| RULE_14 | DSCR de mercado -1,46x | Hallazgo del deal: con ocupación INE no hay servicio de deuda | Ancla downside; no apalancar | Demanda probada |
| RULE_15 | Equity 49,62% vs 30% asumido | Hallazgo del deal: 35% LTV y stack completo exigen más equity | Aceptar 49,62% o redimensionar | 521.090,22 € + terreno |
| RULE_10 | Ocupación 31,36% = 1,48x INE 21,24% | Hallazgo del deal: el caso es upside, no base | Etiquetar como upside; test Fase 0 | Reservas u ocupación ≥ 45% |
| RULE_07 | DSRA pasa en 13.823,82 €, seis meses exactos | Hallazgo del deal: sin colchón frente al CVaR 99% de 62.786,01 € | Dimensionar la DSRA al CVaR | Fuente y equity adicional |

## 8. Base de precios e inflación

Reforma y R7 están en euros constantes de 2026: ADR, OPEX y nómina son planos en términos reales. No se indexan los ingresos para evitar un desajuste nominal/real que inflaría valor terminal y TIR; el cap rate se aplica a un EBITDA real. El stress es asimétrico: suben los costes reales, no los precios; es compresión de margen, no previsión.

| Inflación real de costes | EBITDA A5 | DSCR A5 | Gap neto |
|---:|---:|---:|---:|
| 0,0% | 155.713 € | 3,15x | +49.147 € |
| 2,0% | 136.912 € | 2,78x | -142.819 € |
| 2,5% | 132.035 € | 2,69x | -192.609 € |
| 3,0% | 127.087 € | 2,59x | -243.134 € |

El DSCR aguanta porque la deuda se dimensionó sobre el CFADS mínimo; el valor no. Con 2% de inflación real de costes, el caso base no pasa el test neto. El 3,2% no es holgura.

## 9. Control de cambios y reproducibilidad

Cualquier cambio en `assumptions.py`, `config/reform.py` o los motores se registra con SHA y fecha, reejecuta los 73 tests y el pipeline, compara los JSON, regenera el Excel, verifica las 2.060 fórmulas, actualiza este log y se aprueba antes de publicar.

**Cómo ejecutarlo:**

```bash
pip install -r requirements.txt
python main.py                 # 15 pasos
python main.py --no-charts
python -m pytest tests/ -q     # 73 tests
```

Salidas: Excel de 13 pestañas y dos JSON. Monte Carlo: 1.000 iteraciones; cópulas: 50.000; semilla 42. La reproducibilidad es numérica en el mismo entorno Python 3.11 y dependencias; no se garantiza copia idéntica entre librerías o sistemas. No se editan a mano el Excel ni los JSON.

## 10. Limitaciones y firma

El modelo no sustituye una auditoría independiente. No hay ofertas de construcción vinculantes, booking curve ni competitive set; LEADER no tiene carta de concesión; la fiscalidad es simplificada; el motor mensual es un stress de liquidez; la salida por cap rate no incorpora tasación; y R7 pasa por solo 3,2%, con 110 k€ por cabaña como benchmark. El playbook de distress no es un análisis de liquidación. No hay revisión de terceros: este documento describe el control interno y no certifica resultados.

| Rol | Nombre | Fecha | Estado |
|---|---|---|---|
| Responsable del modelo | _[pendiente]_ | _[pendiente]_ | Borrador |
| Preparador | _[pendiente]_ | _[pendiente]_ | Borrador |
| Revisor independiente | _[pendiente]_ | _[pendiente]_ | No realizado |
| Aprobador de crédito | _[pendiente]_ | _[pendiente]_ | No realizado |

**Nota:** no ha habido revisión de terceros. La firma del revisor exigiría un encargo separado y acceso a los libros fuente y a las ofertas de construcción.
