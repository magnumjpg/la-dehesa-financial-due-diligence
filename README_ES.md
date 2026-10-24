# La Dehesa del Castrillo S.L.

### Viabilidad hostelera, underwriting de deuda senior y due diligence computacional

**Modelo financiero de portfolio construido a partir de mi propio trabajo de fin de grado.**
Python 3.11 · 41 tests automatizados · modelo Excel de 12 pestañas · pipeline de 14 pasos

[![tests](https://github.com/magnumjpg/la-dehesa-financial-due-diligence/actions/workflows/tests.yml/badge.svg)](https://github.com/magnumjpg/la-dehesa-financial-due-diligence/actions/workflows/tests.yml)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

> **Lee esto primero.** Esto no es un pitch de "operación segura". El caso promotor original genera 86.275 € de ingresos en el año 1, 11.297 € de EBITDA y caja negativa. Con la ocupación oficial del INE para Segovia (21,24%), el proyecto no cubre el servicio de deuda en el año 1 (DSCR 0,40x). El caso principal en Python (31,36% de ocupación madura, 28,23% en el año 1) es un **caso de gestión / upside**, no una previsión de mercado, y es el único que cumple el covenant de 1,25x. La auditoría está deliberadamente permitida fallar: **pasan 8 de 14 reglas, quedan 5 excepciones materiales y 1 warning**, y el veredicto es `CONDITIONAL - 5 MATERIAL EXCEPTION(S)`.

---

## 1. Qué es este proyecto

Partí de mi propio trabajo universitario: un estudio de viabilidad para una finca rural de 25 hectáreas en Segovia (7 habitaciones dobles, una casa rural completa, un restaurante de 21 cubiertos y una biopiscina natural). El Excel original es un simulador promotor de una sola hoja con fórmulas vivas; usa una ocupación del 19,2%. El Word documenta una ocupación más conservadora del 16,5–17%, contratos a tiempo parcial y una solicitud de ayuda LEADER. Esa diferencia entre el Word y el Excel es lo primero que tuvo que reconciliar la auditoría.

Después reconstruí el análisis en Python para responder a las preguntas que el trabajo original no podía responder:

- ¿Qué pasa con la **ocupación oficial del INE** en lugar del supuesto del promotor?
- ¿Se **financia de verdad el proyecto al cierre**, una vez incluidos los costes de preapertura, el circulante y una reserva de servicio de deuda?
- ¿Es la **nómina legal por hora** según el convenio de hostelería de Segovia y el SMI de 2026?
- ¿El **puente de IVA** crea caja o solo la mueve?
- ¿Puede la **Fase II** autofinanciarse con la caja de la Fase I, o es un doble gasto de la subvención y del reembolso de IVA?
- ¿Cómo son los retornos **con y sin salida**?

La capa Python no es un lavado de cara. Añade una arquitectura de tres casos, un motor de fuentes y usos, una auditoría computada, un libro Excel con fórmulas vivas y una batería de tests que fija los números honestos.

---

## 2. Tres casos, uno al lado del otro

| Caso | Ocupación madura | Ingresos A1 | EBITDA A1 | DSCR A1 | Caja A1 | TIR proyecto (sin salida) | TIR proyecto (salida 8,5%) | TIR equity (salida 8,5%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Gestión (upside)** | 31,36% | 154.548 € | 66.086 € | 1,34x | 10.790 € | −20,89% | 15,43% | 29,74% |
| **Mercado INE** | 21,24% | 95.555 € | 17.621 € | 0,40x | −29.915 € | −27,31% | 9,63% | 17,43% |
| **Promotor (Excel original)** | 19,20% | 86.275 € | 11.297 € | 0,33x | −2.553 € | −29,48% | 6,84% | 10,95% |

**Qué es cada caso:**

- **Promotor** — réplica fiel del Excel universitario original: 19,2% de ocupación (491 habitaciones-noche sobre 2.555 disponibles), ADR de 85 € en habitación, 380 € en casa, ticket de restaurante de 20 €, deuda al 4,5% a 25 años y sin subvención. El modelo Python reproduce los ingresos y el EBITDA originales al euro y la caja del año 1 con una diferencia de 7 € (original ≈ −2.560 €; modelo −2.553,20 €). Es el caso que el autor realmente suscribió.
- **Mercado INE** — el benchmark independiente: 21,24% de ocupación oficial de Segovia en 2025 (INE EOTR, tabla 2070), con los unit economics originales y la misma deuda. Es lo más parecido a un caso de mercado dentro del libro.
- **Gestión (upside)** — el caso principal en Python: 31,36% de ocupación madura (1,48x la media del INE), una comida por huésped y día a 25 €, deuda senior al 5,5% y la subvención LEADER de 163.000 € en el mes 14. Es un upside operativo, no un caso base.

Los tres casos comparten CapEx, tipo impositivo y mecánica de balance. La diferencia está en la demanda y en los unit economics, que es exactamente donde reside el riesgo.

---

## 3. Los hallazgos que importan

1. **El Excel original es el caso promotor, no el caso base.** Genera 86.275 € de ingresos y 11.297 € de EBITDA. Los 154.548 € / 66.086 € del modelo Python publicado son un upside de gestión, no una corrección del original.
2. **El caso de mercado INE no cubre el servicio de deuda en el año 1.** Con 21,24% de ocupación, el EBITDA es 17.621 €, el DSCR es 0,40x y la caja del año 1 es −29.915 €. El proyecto solo funciona si la ocupación supera materialmente la media provincial.
3. **El caso de gestión cumple el covenant con un 28,23% en el año 1 y un 31,36% en el año 2.** El DSCR es 1,34x en el año 1, 1,64x en el año 2 y 1,73x en el año 3. Eso es 1,48x la media del INE en madurez, que es el supuesto comercial central que hay que defender. Ojo: el P&L anual usa una pila de costes simplificada; con la pila completa de unit economics (OTA, amenities, desayuno), el punto muerto del covenant es 28,44% y el margen de seguridad es mucho más fino.
4. **Hay un gap de financiación de 70.768 € al cierre.** Los usos al cierre son 948.858 € (CapEx 729.000 € + IVA soportado 153.090 € + preapertura 25.000 € + circulante 20.000 € + DSRA de 6 meses 21.768 €). Las fuentes al cierre son 878.090 € (deuda 507.500 € + equity 217.500 € + puente de IVA 153.090 €). La subvención LEADER de 163.000 € llega en el mes 14 y no puede financiar el cierre. Con los usos omitidos, la caja del año 1 de gestión es **−55.978 €**, no +10.790 €.
5. **La línea de crédito es incoherente.** El modelo dispone de un puente de IVA de 143.596 € en el caso de gestión, 147.285 € en el de mercado y 166.752 € en el promotor, mientras que la línea revolvente declarada es de 50.000 €. El puente debe revelarse como una facilidad separada o la línea debe ampliarse.
6. **La Fase II no se autofinancia.** La Fase II necesita 435.564 € (359.970 € de CapEx neto + 75.593,70 € de IVA). La Fase I genera 193.950 € de caja al final del año 2. El gap del phase-gate es **−241.614 €**, por lo que el gate devuelve `DO NOT PROCEED`. La antigua afirmación de "100% autofinanciada" era un doble gasto de la subvención LEADER y del reembolso de IVA.
7. **Los retornos dependen de la salida.** Sin salida, la TIR del proyecto a 5 años es negativa en los tres casos (−20,89% gestión, −27,31% mercado, −29,48% promotor). Con una salida a cap rate del 8,5%, la TIR del proyecto de gestión es 15,43% y la del equity es 29,74%. La salida, no el flujo operativo, es lo que mueve el retorno.
8. **La auditoría es computada y puede fallar.** Pasan 8 de 14 reglas. Las cinco excepciones materiales son la caja ajustada, las fuentes y usos, el límite de la línea de crédito, la autofinanciación de la Fase II y el DSCR de mercado. El warning es la ocupación de gestión frente al INE. Ese es el sentido de la capa de auditoría: reporta lo que el modelo hace de verdad, no lo que la narrativa quiere.
9. **La nómina es a tiempo parcial y cumple por hora.** El Word original documenta unas 1.900 horas para dos cocineros y 1.792 horas de limpieza. El modelo refinado usa 950 + 950 + 1.792 = 3.692 horas (2,09 FTE). El bruto por hora es 14,21 € para los cocineros y 9,77 € para limpieza, por encima del SMI 2026 (9,69 €) y del mínimo del convenio de Segovia (10,12 € para cocinero, 9,02 € para auxiliar). La comparación anterior de "3 FTE a convenio completo" era errónea; el riesgo que queda es de planificación y cobertura, no de precio/hora.
10. **Las afirmaciones "BB+ investment grade" y "escudo de BINs" eran incorrectas.** BB+ es sub-investment-grade, no investment grade. El caso de gestión tiene EBT positivo desde el año 1 (31.041 €) y paga 7.760 € de impuesto de sociedades; no tiene escudo de BINs. Ambas afirmaciones se han eliminado de la narrativa del modelo.

---

## 4. Original vs refinado: la reconciliación

| Categoría | Excel original | Refinado: gestión / mercado / promotor | Notas |
|---|---|---|---|
| Ocupación (madura) | 19,20% | 31,36% / 21,24% / 19,20% | Gestión es 1,48x el INE; promotor es el original. |
| Ingresos A1 | 86.275 € | 154.548 € / 95.555 € / 86.275 € | Gestión añade 1 comida/huésped/día a 25 €. |
| EBITDA A1 | 11.297 € | 66.086 € / 17.621 € / 11.297 € | El promotor coincide con el original al euro. |
| Caja final A1 | ≈ −2.560 € | 10.790 € / −29.915 € / −2.553 € | La caja negativa original es un gap real de financiación. |
| DSCR A1 | n/a | 1,34x / 0,40x / 0,33x | Solo gestión supera 1,25x. |
| CapEx | 725.000 € | 729.000 € | Incluye 4.000 € de Kit Digital. |
| Nómina (anual) | 58.740 € | 60.075 € | Horas a tiempo parcial; incluye SS empresarial. |
| IVA soportado CapEx | No modelado | 153.090 € bruto / 143.596 € puente | 21% deducible; el puente es financiación. |
| IVA repercutido | No modelado (ingresos netos) | 10,0% legal | El Excel original no aplicaba el 21% a las ventas. |
| Balance | Una hoja, sin balance | Activo = Pasivo + Patrimonio (0,00 €) | Doble partida estricta, 5 años, 3 casos. |

### La corrección de la "trampa del IVA"

El README anterior afirmaba que aplicar el 21% de IVA a las ventas de hostelería creaba un déficit de caja de −152.250 € en el año 1, y que corregirlo al 10% "confirmaba la solvencia" en +60.750 €. **Eso no es lo que hace el Excel original.** La hoja original trabaja en ingresos netos y no aplica el 21% de IVA repercutido a las ventas. Su caja negativa del año 1 es un gap real de financiación, no un artefacto del IVA.

El modelo refinado sí aplica el tipo legal del 10% para hostelería (Ley 37/1992, art. 91.Uno.2.2ª) y sí reconoce el 21% de IVA soportado en CapEx como activo deducible. Pero el puente que financia ese IVA soportado es una **fuente de financiación**, no una subvención:

- Se dispone al cierre (153.090 € en el motor de financiación; 143.596 € neto de IVA repercutido en el modelo anual).
- Devenga un 5,5% de interés. El modelo anual carga un año completo de intereses del puente en el año 2 (7.897,80 €), que es la razón por la que el beneficio neto del año 2 es 29.583 € y no 35.506 €.
- Se repaga con el reembolso de la AEAT en el mes 18. El reembolso no es una segunda entrada de caja.

La conclusión honesta es: **la caja negativa original es un gap de financiación, y el caso de gestión solo es solvente por la ocupación upside y por el puente.** La corrección del IVA cambia el calendario y la estructura de financiación; no crea 213.000 € de valor.

---

## 5. Calibración de demanda: INE vs promotor vs gestión

La *Encuesta de Ocupación en Alojamientos de Turismo Rural* (EOTR) del INE, tabla 2070 para Segovia, registra:

| Periodo | Ocupación por habitaciones | Habitaciones-noche ocupadas |
|---|---:|---:|
| 2023 | 21,32% | — |
| 2024 | 21,50% | — |
| 2025 | **21,24%** | 77,5 días |
| Agosto 2025 | 36,78% | — |
| Enero 2025 | 9,58% | — |

El caso de gestión usa una serie mensual calibrada a la media anual de 21,24% de 2025, conservando los anclajes de enero y agosto. Tras el ramp-up de 2026 (90% en el año 1, 100% en el año 2, 105% desde el año 3), el caso de gestión alcanza 28,23% en el año 1, 31,36% en el año 2 y 32,93% en el año 3. El motor mensual muestra el valle de invierno en marzo y el pico de verano en agosto.

El caso promotor usa el 19,2% del Excel original (491 habitaciones-noche / 2.555 disponibles). El caso de mercado usa el 21,24% con los unit economics originales. La diferencia entre 19,2% y 31,36% es el riesgo comercial que el modelo está suscribiendo.

---

## 6. Unit economics (USALI y costeo marginal)

| Métrica | Valor |
|---|---:|
| Capacidad | 8 llaves (7 habitaciones dobles + 1 casa rural) = 2.920 unidad-noches/año |
| Ingreso bruto diario al 100% | 1.500 € (975 € alojamiento + 525 € F&B) |
| Coste variable por día ocupado | 280,25 € (18,7%) |
| — COGS F&B (30%) | 157,50 € |
| — Comisiones OTA (60% al 15%) | 87,75 € |
| — Amenities y suministros | 35,00 € |
| Margen de contribución unitario | 1.219,75 € por día ocupado (81,32%) |
| Margen por habitación-noche | 107,97 € por habitación-noche (79,98%) |
| Overhead fijo anual | 72.234 € (nómina 60.075 € + opex 12.159 €) |
| Servicio de deuda senior | 43.536,35 € (amortización francesa 15 años al 3,5%) |
| Carga fija anual total | 115.770,35 € |

**Umbrales de punto muerto:**

| Umbral | Días ocupados | Ocupación |
|---|---:|---:|
| Punto muerto operativo (EBITDA = 0) | 59,2 | 16,22% |
| Punto muerto de servicio de deuda (DSCR = 1,00x) | 94,9 | 26,00% |
| Covenant bancario (DSCR ≥ 1,25x) | 103,8 | 28,44% |

Esta es la forma más clara de ver el problema: el 19,2% del promotor está por encima del punto muerto operativo pero **por debajo** del punto muerto de servicio de deuda del 26,00%, así que el caso original no puede pagar su deuda con la operación. El 31,36% del caso de gestión está por encima del covenant del 28,44%, pero solo por unos 2,9 puntos porcentuales. El modelo anual de tres estados pasa el año 1 con un 28,23% porque usa una pila de costes simplificada; el umbral del 28,44% es la visión más estricta de unit economics y es la que debería usar un comité de crédito.

---

## 7. Nómina: tiempo parcial, no 3 FTE

El Word original documenta contratos a tiempo parcial: unas 1.900 horas entre dos cocineros y 1.792 horas de limpieza. El modelo refinado usa:

| Rol | Horas anuales | FTE | Bruto/hora | SMI 2026 | Mínimo convenio Segovia | ¿Cumple? |
|---|---:|---:|---:|---:|---:|---|
| Cocinero 1 | 950 | 0,54 | 14,21 € | 9,69 € | 10,12 € | Sí |
| Cocinero 2 | 950 | 0,54 | 14,21 € | 9,69 € | 10,12 € | Sí |
| Limpieza / auxiliar | 1.792 | 1,01 | 9,77 € | 9,69 € | 9,02 € | Sí |
| **Total** | **3.692** | **2,09** | — | — | — | — |

El SMI 2026 es 17.094 € brutos anuales (14 pagas de 1.221 €, Real Decreto 126/2026). El convenio de hostelería de Segovia (2026) fija la referencia de cocinero en 17.844,16 € y la de auxiliar en 15.916,22 €; dividido por las horas anuales relevantes, los mínimos por hora son 10,12 € y 9,02 €. Los brutos por hora del modelo están por encima de ambos mínimos.

Los 58.740 € del Excel original son nómina bruta (35.640 € cocineros + 23.100 € limpieza). Los 60.075 € del modelo refinado incluyen seguridad social empresarial y la estructura de horas a tiempo parcial. La diferencia no es un error de nómina; es una base de coste distinta. La afirmación anterior de que el modelo empleaba "3 FTE a convenio completo" era errónea y se ha eliminado.

---

## 8. Modelo de tres estados y réplica del promotor

El modelo genera cuenta de resultados, estado de flujos de caja y balance para cinco años. La fórmula de ingresos del caso de gestión es:

```
Ingresos = 365 × ocupación × (7 habitaciones × 85 € + 1 casa × 380 € + 21 comidas × 25 €)
```

Los casos de mercado y promotor usan los unit economics originales (85 € / 380 € / 20 €, 859 comidas al 19,2%, escaladas al 21,24% en el caso de mercado). La deuda es una amortización francesa a 15 años al 3,5% en gestión/mercado y al 4,5% a 25 años en el promotor. El impuesto es el 25% del EBT positivo; el caso de gestión paga impuestos desde el año 1, así que no hay escudo de BINs.

**Comprobación de réplica del promotor:**

| Línea | Excel original | Caso promotor Python | Diferencia |
|---|---:|---:|---:|
| Ingresos A1 | 86.275 € | 86.275,00 € | 0,00 € |
| EBITDA A1 | 11.297 € | 11.297,00 € | 0,00 € |
| Caja final A1 | ≈ −2.560 € | −2.553,20 € | ≈ 7 € |
| Discrepancia de balance | n/a | 0,00 € | — |

La identidad de balance (Activo = Pasivo + Patrimonio) se cumple con 0,00 € en los tres casos y los cinco años. Se comprueba en los tests y en la pestaña `Live Model` del Excel.

---

## 9. Financiación: fuentes y usos, gap y línea de crédito

| Caso | Usos al cierre | Fuentes al cierre | Gap al cierre | Caja ajustada A1 | DSCR A1 | Línea dispuesta | Estado |
|---|---:|---:|---:|---:|---:|---:|---|
| Gestión | 948.858 € | 878.090 € | **−70.768 €** | **−55.978 €** | 1,34x | 143.596 € | Infrafinanciado |
| Mercado | 948.858 € | 878.090 € | **−70.768 €** | **−96.684 €** | 0,40x | 147.285 € | Infrafinanciado |
| Promotor | 939.175 € | 897.250 € | **−41.925 €** | **−64.478 €** | 0,33x | 166.752 € | Infrafinanciado |

**Usos al cierre (gestión):**

| Uso | Importe |
|---|---:|
| CapEx (neto de IVA) | 729.000,00 € |
| IVA soportado (21%) | 153.090,00 € |
| Costes de preapertura | 25.000,00 € |
| Circulante inicial | 20.000,00 € |
| DSRA (6 meses de servicio de deuda) | 21.768,18 € |
| **Total usos** | **948.858,18 €** |

**Fuentes al cierre:**

| Fuente | Importe |
|---|---:|
| Deuda senior (70%) | 507.500,00 € |
| Equity promotor (30%) | 217.500,00 € |
| Puente de reembolso de IVA | 153.090,00 € |
| Línea de crédito al cierre | 0,00 € |
| **Total fuentes** | **878.090,00 €** |
| Subvención LEADER (mes 14, post-cierre) | 163.000,00 € |
| **Total incluyendo subvención** | **1.041.090,00 €** |

La subvención es real, pero es **post-cierre**. El gap al cierre es 70.768,18 €; la inyección de equity recomendada es exactamente esa cantidad. Si se incluye la subvención, la posición total de financiación es positiva (92.231,82 €), pero el proyecto es ilíquido al cierre.

**Incoherencia de la línea de crédito.** El modelo anual dispone un puente de IVA de 143.596 € en el caso de gestión. La línea revolvente declarada es de 50.000 €. El puente es una facilidad separada con un 5,5% de interés, no la línea operativa. El modelo debe revelarlo como facilidad separada o ampliar la línea a al menos 150.000 €. La auditoría lo marca como excepción material.

**DSRA.** El motor de financiación usa seis meses de servicio de deuda (21.768,18 €). El análisis CVaR 99% del comité de crédito recomienda 47.596,85 €. Si se usa el DSRA mayor, el gap al cierre se amplía en 25.828,67 €, hasta unos 96.597 €. Es un punto de term sheet, no un error de redondeo.

---

## 10. Retornos: la salida es la que hace el trabajo

| Caso | TIR proyecto (sin salida) | TIR proyecto (salida 8,5%) | TIR equity (salida 8,5%) | Valor terminal | MOIC proyecto | MOIC equity |
|---|---:|---:|---:|---:|---:|---:|
| Gestión | −20,89% | 15,43% | 29,74% | 1.048.704 € | 1,90x | 3,73x |
| Mercado | −27,31% | 9,63% | 17,43% | 898.396 € | 1,54x | 2,52x |
| Promotor | −29,48% | 6,84% | 10,95% | 796.462 € | 1,36x | 1,82x |

El valor terminal es el EBITDA del año 5 capitalizado a un cap rate del 8,5%. Sin salida, el flujo operativo de cinco años no recupera el CapEx de 729.000 € en ningún caso. La TIR de proyecto de gestión del 15,43% está por debajo de un hurdle típico de private equity del 18–20%; la TIR de equity del 29,74% está apalancada y depende de la salida. Los casos de mercado y promotor están por debajo de un hurdle razonable incluso con la salida.

Esto contrasta deliberadamente con el README anterior, que reportaba una TIR media del sponsor del 18,4% a partir de un Monte Carlo que no modelaba la salida ni el gap de financiación. Los retornos actuales se calculan a partir de la serie de flujos, con un solver de TIR Newton/bisección y un valor terminal explícito.

---

## 11. Stress-testing de escenarios

| Métrica | Conservador A1 | Conservador A3 | Base A1 | Base A3 | Optimista A1 | Optimista A3 |
|---|---:|---:|---:|---:|---:|---:|
| Ingresos | 124.798 € | 145.597 € | 154.548 € | 180.306 € | 204.003 € | 238.004 € |
| EBITDA | 32.236 € | 50.852 € | 66.086 € | 89.140 € | 111.794 € | 142.224 € |
| Beneficio neto | −10.309 € | 10.753 € | 23.281 € | 41.993 € | 59.431 € | 83.513 € |
| Caja final | −19.923 € | 134.218 € | 10.790 € | 225.556 € | 45.927 € | 340.430 € |
| DSCR | 0,67x | 1,06x | 1,34x | 1,73x | 2,19x | 2,72x |
| ICR | 1,30x | 2,27x | 3,81x | 5,77x | 7,53x | 10,80x |

El caso conservador incumple el covenant en el año 1 (0,67x) y termina con caja negativa. El caso base es el upside de gestión. El optimista es una sensibilidad, no una previsión.

---

## 12. Monte Carlo y riesgo de cola con cúpulas

**Monte Carlo gaussiano naïve (N = 1.000):**

| Métrica | Valor |
|---|---:|
| DSCR medio año 1 | 1,36x |
| DSCR mediano año 1 | 1,34x |
| VaR 95% (percentil 5) | 0,88x |
| P(incumplimiento de covenant, DSCR < 1,25x) | 35,4% |
| P(insolvencia, DSCR < 1,00x) | 9,6% |

**Cúpulas multivariantes (50.000 simulaciones):**

| Modelo | DSCR medio | DSCR mediano | VaR 95% | VaR 99% | CVaR 99% | P(DSCR < 1,25x) | P(DSCR < 1,00x) | Déficit CVaR 99% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Gaussiana | 1,36x | 1,34x | 0,64x | 0,37x | 0,26x | 42,31% | 21,61% | 33.906 € |
| Student-t (ν = 4) | 1,36x | 1,34x | 0,64x | 0,35x | 0,21x | 42,11% | 21,23% | 36.735 € |
| Clayton (θ = 1,8) | 1,36x | 1,38x | 0,49x | 0,17x | 0,04x | 40,35% | 23,23% | 47.597 € |

La cúpula Clayton captura la dependencia asimétrica de la cola inferior: en un mal año, la ocupación, el ADR y el gasto en restaurante se deterioran a la vez. El DSRA recomendado por el comité de crédito es 47.596,85 €, que cubre el déficit CVaR 99% de Clayton. El Monte Carlo gaussiano se mantiene como benchmark, no como modelo de riesgo.

---

## 13. Fase II: suites de paisaje y balsa biológica

La Fase II añade dos suites de paisaje de 55 m² y una balsa biológica de 200 m³. El CapEx all-in es 359.970 € netos, más 75.593,70 € de IVA soportado, para una necesidad de caja de 435.563,70 €.

| Componente de CapEx | Importe |
|---|---:|
| Ejecución de obra (PEM) | 260.000,00 € |
| Ejecución con honorarios e impuestos (PEC) | 309.400,00 € |
| Honorarios de ingeniería y arquitectura | 23.400,00 € |
| Impuestos municipales (ICIO) | 11.700,00 € |
| Reserva de contingencia | 15.470,00 € |
| **CapEx all-in neto** | **359.970,00 €** |
| IVA soportado (21%) | 75.593,70 € |
| **Necesidad de caja** | **435.563,70 €** |

**Escenarios operativos (año 3 estabilizado):**

| Escenario | Ocupación | ADR | EBITDA incremental | TIR con salida 8,5% |
|---|---:|---:|---:|---:|
| Base (sin FTE incremental) | 50,0% | 290 € | 99.620,52 € | 40,29% |
| Realista (1 FTE) | 45,0% | 270 € | 51.435,20 € | 19,64% |
| Estrés (1 FTE) | 36,4% | 250 € | 25.185,88 € | 2,07% |
| Conservador | 40,0% | 250 € | 31.870,20 € | 7,50% |
| Optimista | 58,0% | 330 € | 142.432,65 € | 53,34% |

El caso base es deliberadamente agresivo: el 50% de ocupación es más del doble de la media provincial del INE y asume cero FTE incremental. El caso realista (45% de ocupación, un FTE adicional) es el mejor anclaje de underwriting. El caso de estrés es apenas positivo.

**Phase gate:**

| Test | Valor |
|---|---:|
| DSCR Fase I año 3 | 1,73x (mínimo 1,25x) → pasa |
| Caja Fase I al final del año 2 | 193.949,95 € |
| Necesidad de caja Fase II | 435.563,70 € |
| Gap de financiación Fase II | **−241.613,75 €** |
| Recomendación del gate | **NO PROCEDER** — se requiere financiación adicional o un alcance menor |

El README anterior afirmaba que la Fase II estaba 100% autofinanciada con 421.784 € de tesorería bruta. Esa cifra incluía la subvención LEADER y el reembolso de IVA, ambos ya comprometidos en la Fase I. El tratamiento correcto es un phase gate: la Fase II solo puede proceder si se cumplen los covenants de la Fase I y la caja de la Fase I cubre la necesidad de la Fase II. No es el caso.

Si la Fase II se financiara, los ingresos consolidados del año 3 serían 326.488,50 € y el EBITDA 188.760,39 €, con el DSCR expandiéndose de 1,73x a 4,34x (asumiendo que no hay nueva deuda senior). Es un upside real, pero condicionado a la financiación, no automático.

---

## 14. Auditoría computada: 14 reglas, 8 pasan, 5 materiales, 1 warning

La auditoría se calcula desde el modelo, no se escribe a mano. Está permitida fallar.

| Regla | Severidad | Estado | Valor real | Umbral |
|---|---|---|---:|---:|
| RULE_01_BALANCE_SHEET_EQUALITY | Material | **PASA** | 0,00 € | ≤ 0,01 € |
| RULE_02_HOSPITALITY_VAT_RATE | Material | **PASA** | 10,0% | 10,0% |
| RULE_03_CAPEX_INPUT_VAT | Material | **PASA** | 153.090 € | 153.090 € |
| RULE_04_PAYROLL_HOURLY_COMPLIANCE | Material | **PASA** | 9,77 € mín. | ≥ 9,02 € |
| RULE_05_MANAGEMENT_DSCR | Material | **PASA** | 1,34x | ≥ 1,25x |
| RULE_06_ADJUSTED_CASH_TROUGH | Material | **FALLA** | −55.978,44 € | ≥ 0 € |
| RULE_07_DSRA_SIZING | Warning | **PASA** | 21.768,18 € | ≥ 6 meses |
| RULE_08_SOURCES_USES_CLOSE | Material | **FALLA** | −70.768,18 € | ≥ 0 € |
| RULE_09_CREDIT_LINE_LIMIT | Material | **FALLA** | 143.596,37 € | ≤ 50.000 € |
| RULE_10_OCCUPANCY_VS_INE | Warning | **FALLA** | 1,48x | ≤ 1,25x |
| RULE_11_PHASE2_SELF_FUNDING | Material | **FALLA** | −241.613,75 € | ≥ 0 € |
| RULE_12_RETURNS_VS_WACC | Material | **PASA** | 15,43% | ≥ 8,0% |
| RULE_13_PROMOTER_REPLICATION | Info | **PASA** | 86.275 € / 11.297 € | exacto |
| RULE_14_MARKET_DSCR | Material | **FALLA** | 0,40x | ≥ 1,25x |

**Veredicto:** `CONDITIONAL - 5 MATERIAL EXCEPTION(S)`.

Las cinco excepciones materiales son el gap de financiación, el valle de caja ajustada, la incoherencia de la línea de crédito, el doble gasto de la Fase II y el DSCR de mercado. El warning es el supuesto de ocupación de gestión (1,48x la media del INE). El JSON de auditoría se exporta a `data/model_audit_summary.json` y las mismas reglas se reproducen en la pestaña `Funding & Audit` del Excel.

---

## 15. El modelo Excel

El libro tiene **12 pestañas** y **172 fórmulas**:

| Pestaña | Propósito |
|---|---|
| `Read Me & Checks` | Mapa del modelo, tres casos, comprobaciones de integridad y hallazgos principales. |
| `Inputs` | Todos los supuestos codificados en un solo sitio (celdas azules). |
| `Live Model` | P&L, caja, deuda y balance a 5 años con fórmulas; replica el caso de gestión. |
| `Funding & Audit` | Fuentes y usos, gap, coherencia de la línea, phase gate de Fase II y reglas de auditoría. |
| `Executive Scorecard` | Scorecard de underwriting de una página. |
| `3-Statement Model` | Salida completa de Python: P&L, caja y balance. |
| `Debt Schedule` | Amortización francesa a 15 años. |
| `Scenario Stress-Testing` | Conservador / base / optimista y sensibilidad 2D de DSCR. |
| `Monte Carlo Risk` | Simulación estocástica de riesgo de crédito con 1.000 iteraciones. |
| `Credit Risk & Copula` | Comparativa de colas gaussiana / Student-t / Clayton. |
| `Unit Economics & Runway` | RevPAR, TRevPAR, margen de contribución y stress de liquidez mensual. |
| `Phase II Expansion` | Suites y balsa: CapEx, P&L, escenarios, phase gate e impacto consolidado. |

El `Live Model` es intencionadamente simple y transparente: los ingresos son una fórmula ligada a `Inputs`, la deuda viene de `Debt Schedule` y las comprobaciones comparan la salida viva con Python. Las 172 fórmulas son:

- 161 en `Live Model`;
- 8 en `Read Me & Checks`;
- 3 en `Funding & Audit`.

Las pestañas de informe son snapshots de Python y no recalculan. El libro no tiene motor de cálculo propio; ábrelo en Excel o LibreOffice para recalcular. Las fórmulas se han validado con una réplica en Python: ingresos, EBITDA, DSCR y caja final coinciden con el modelo anual al céntimo, y la comprobación de balance está dentro de 1 € (redondeo).

La pestaña `Funding & Audit` puede mostrar `FAIL`. Es la auditoría funcionando como debe.

---

## 16. Arquitectura del repositorio

```
proyecto-dehesa-del-castrillo/
├── main.py                       # Pipeline de 14 pasos
├── README.md / README_ES.md
├── requirements.txt
├── .github/workflows/tests.yml   # CI: tests + pipeline
├── src/
│   ├── config/
│   │   ├── assumptions.py        # CapEx, nómina, deuda, opex, casos, campos de financiación
│   │   └── ine_weights.py        # Serie mensual INE Segovia (calibrada al 21,24%)
│   ├── core/
│   │   ├── statements.py         # Motor de tres estados, tres casos, réplica del promotor
│   │   ├── debt.py               # Amortización francesa
│   │   ├── tax.py                # IVA e impuesto de sociedades
│   │   ├── metrics.py            # DSCR, ICR, TIR (Newton + bisección), retornos con salida
│   │   ├── funding.py            # Fuentes y usos, gap, línea de crédito, phase gate
│   │   ├── unit_economics.py     # Unit economics USALI y puntos muertos
│   │   ├── monthly_cash.py       # Stress de liquidez mensual (sin/con inyección)
│   │   ├── expansion.py          # CapEx Fase II, escenarios, phase gate
│   │   ├── credit_committee.py   # DSRA y memo de underwriting
│   │   └── model_audit.py        # Auditoría computada, 14 reglas, export JSON
│   ├── data/
│   │   ├── extract_raw.py        # Reconciliación con el Excel original
│   │   ├── export_excel.py       # Libro de 12 pestañas
│   │   └── live_excel.py         # Pestañas vivas con fórmulas
│   ├── scenarios/
│   │   └── scenario_analysis.py  # Conservador / base / optimista
│   ├── simulation/
│   │   ├── monte_carlo.py        # Monte Carlo gaussiano naïve
│   │   └── copula_engine.py      # Gaussiana / Student-t / Clayton
│   └── visualization/
│       └── charts.py             # Figuras institucionales
├── tests/
│   ├── test_assumptions.py
│   ├── test_cases.py             # Tests de tres casos y retornos
│   ├── test_funding.py           # Fuentes y usos, gap, phase gate
│   ├── test_model_audit.py       # Auditoría: 8/14, 5 materiales, 1 warning
│   ├── test_expansion.py         # Escenarios de Fase II y phase gate
│   ├── test_financial_engine.py
│   ├── test_unit_economics_monthly.py
│   ├── test_simulation.py
│   └── test_copula.py
├── raw_data/                     # Libros fuente de la reconciliación
│   ├── La_Dehesa_de_Castrillo_Proyecto.xlsx
│   └── Presentacion_La_Dehesa.xlsx
├── data/
│   ├── La_Dehesa_del_Castrillo_Financial_Model.xlsx
│   └── model_audit_summary.json
└── assets/
    └── figure_*.png
```

---

## 17. Instalación y ejecución

```bash
git clone https://github.com/magnumjpg/la-dehesa-financial-due-diligence.git
cd la-dehesa-financial-due-diligence
pip install -r requirements.txt

# Pipeline completo (14 pasos, gráficos, Excel, JSON de auditoría)
python main.py

# Sin generación de gráficos
python main.py --no-charts

# Batería de tests (41 tests)
python -m pytest tests/ -q
```

**Salidas:**

- `data/La_Dehesa_del_Castrillo_Financial_Model.xlsx` — 12 pestañas, 172 fórmulas.
- `data/model_audit_summary.json` — auditoría computada, schema 3.0.0.
- `assets/figure_*.png` — figuras institucionales.

El pipeline es determinista por defecto; el Monte Carlo y las cúpulas usan semilla fija (42).

---

## 18. Limitaciones y siguientes pasos

Este es un modelo de portfolio, no un memorando de inversión. Las limitaciones principales son explícitas:

1. **El caso de gestión es un upside.** El 31,36% de ocupación es 1,48x la media provincial del INE. Debe presentarse como caso de gestión, no como caso base.
2. **El motor mensual es un stress de liquidez independiente.** Usa ADR estacional e incluye comisiones OTA y amenities; el modelo anual usa ADR plano y una estructura de costes más simple. No es una reconciliación línea a línea del modelo anual de tres estados.
3. **El Monte Carlo es gaussiano naïve.** El motor de cúpulas es la herramienta de riesgo de cola; la simulación gaussiana se mantiene como benchmark.
4. **El DSRA es incoherente.** El motor de financiación usa seis meses (21.768 €); el comité de crédito recomienda 47.597 € según CVaR 99%. El term sheet debería usar la cifra mayor, que amplía el gap al cierre hasta unos 96.597 €.
5. **El CapEx de Fase II es una estimación pretender.** No hay ofertas de construcción vinculantes; la contingencia es el 5% del PEC.
6. **El modelo fiscal es simplificado.** Usa un tipo de sociedades del 25%, sin grupo de IVA, sin deducciones autonómicas y sin calendario de BINs más allá del año corriente.
7. **El modelo de nómina es a tiempo parcial.** Los precios/hora cumplen, pero quedan riesgos de planificación, cobertura y rotación.
8. **La subvención se asume concedida.** No hay carta de concesión en el repositorio; el timing LEADER se modela en el mes 14.
9. **Los dos libros fuente usados en la reconciliación están incluidos en `raw_data/`.** El informe Word original y el libro vivo de OneDrive no se redistribuyen; el caso promotor está codificado a partir de los valores auditados y replicado en `statements.py`.
10. **El P&L anual todavía usa una pila de costes simplificada.** Incluye COGS de restaurante (30%), pero no las comisiones OTA (9% del alojamiento), amenities (35 €/día) ni el coste del desayuno que sí incluye el motor de unit economics. Añadirlos reduciría el EBITDA de gestión en unos 23,5 k€ (hasta ~42,6 k€) y llevaría el DSCR por debajo de 1,25x. Es la primera prioridad de la siguiente iteración.
11. **El OPEX es bajo para el activo.** Los 12.159 € de opex fijo son finos para un hotel de 550 m² con restaurante y biopiscina; un rango realista es 30.000–40.000 €. El puente de EBITDA de la auditoría muestra el efecto.
12. **No hay reserva de FF&E, periodo de construcción, IDC ni carencia.** Se asume que la reforma abre inmediatamente después del cierre, y el CapEx de reforma de 440.000 € (800 €/m²) está por debajo del rango de mercado de 1.200–1.800 €/m². Ambos son materiales.
13. **La demanda del restaurante es solo de huéspedes.** El modelo asume 21 cubiertos/día de clientes del hotel, sin cubiertos exteriores, eventos ni bebida. El restaurante es el 35% de los ingresos y no está suscrito de forma independiente.

**Siguientes pasos que daría en un mandato real:**

- Sustituir el ADR plano por una curva de reservas y un competitive set riguroso.
- Integrar el motor mensual en el modelo de tres estados con un waterfall de caja.
- Modelar el DSRA, el puente de IVA y la línea de crédito como facilidades separadas con covenants.
- Ejecutar una optimización de debt sizing y un test de lock-up de distribuciones.
- Encargar ofertas de construcción vinculantes y un informe de quantity surveyor para la Fase II.
- Estresar la nómina con un escenario de plantilla a tiempo completo y una inflación salarial del 10%.

---

## 19. Referencias

- **INE**, *Encuesta de Ocupación en Alojamientos de Turismo Rural* (EOTR), tabla 2070, Segovia, 2023–2025.
- **Ley 37/1992**, *Impuesto sobre el Valor Añadido*, art. 91.Uno.2.2ª (tipo del 10% para hostelería) y arts. 92–114 (IVA soportado deducible).
- **Ley 27/2014**, *Impuesto sobre Sociedades*, tipo del 25%.
- **Convenio Colectivo Provincial de Hostelería de Segovia** (2026), tablas salariales de cocineros, camareros y auxiliares.
- **Real Decreto 126/2026**, SMI 2026 (17.094 € brutos/año, 14 pagas de 1.221 €).
- **LEADER / Diputación de Segovia**, marco de ayudas al desarrollo rural (163.000 € asumidos).
- **USALI** (Uniform System of Accounts for the Lodging Industry), 11ª edición, para la estructura de unit economics.
- **Benchmark:** Vivood Landscape Hotel (Alicante), Miluna Open Nature Rooms (Toledo), Basoa Suites (Navarra), Cabañitas del Bosque (A Coruña).

---

### Nota sobre autoría y propósito

Los archivos Excel y Word originales son mi propio trabajo universitario. La capa Python se añadió para demostrar modelización financiera asistida por IA, no para reclamar la autoría del estudio original. El valor del modelo no es que haga que el proyecto parezca mejor; es que hace visibles, cuantificables y testeables sus debilidades. El veredicto `CONDITIONAL` de la auditoría es la salida honesta.
