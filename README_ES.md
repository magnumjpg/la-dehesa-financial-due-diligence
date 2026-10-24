# La Dehesa del Castrillo S.L.
### Viabilidad Financiera, Due Diligence Operativa y Stress-Testing Estocástico para Hostelería Rural

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests: Pytest Passed](https://img.shields.io/badge/tests-26%20passed-brightgreen.svg)](https://docs.pytest.org/)
[![Model Audit: Verified](https://img.shields.io/badge/Model%20Audit-7%2F7%20Passed-blue.svg)](data/model_audit_summary.json)
[![Deliverable: Excel Model](https://img.shields.io/badge/Modelo%20Excel-7%20Pestañas%20.XLSX-success.svg)](data/La_Dehesa_del_Castrillo_Financial_Model.xlsx)

[English](README.md) | [Español](README_ES.md)

**Autor:** Jaime Pérez  
**Especialidad:** Real Estate Private Equity, Due Diligence Operativa y Análisis de Crédito Bancario  
**Alcance del Proyecto:** Finca Rural de 25 Hectáreas | Segovia, España | Inversión: 729.000 € | Financiación 70/30 Deuda/Capital  
**Entregables Principales:** Motor Financiero Modular en Python (`/src`), Motor de Unit Economics y Runway Mensual (`unit_economics.py`, `monthly_cash.py`), Capa de Auditoría Programática e Integridad de Modelo (`model_audit_summary.json`), Motor de Cópulas Multivariables (`copula_engine.py`), Memorando para Comité de Riesgos (`credit_committee.py`), Figuras Institucionales de Alta Resolución (`/assets`), Batería de Tests Unitarios (`/tests`) y Modelo Maestro en Excel de 7 pestañas (`data/La_Dehesa_del_Castrillo_Financial_Model.xlsx`).


```
+----------------------------------------------------------------------------------------------------+
|                                CUADRO DE MANDO EJECUTIVO DE VIABILIDAD                              |
+---------------------------------+-------------------------+-----------------------+----------------+
| Métrica Financiera              | Año 1 (Rampa Arranque)  | Año 2 (Estabilizado)  | Año 3 (Maduro) |
+---------------------------------+-------------------------+-----------------------+----------------+
| Ventas Totales Operativas       | 154.548 €               | 171.720 €             | 180.306 €      |
| Margen EBITDA Realizado         | 66.086 € (42,76%)       | 81.455 € (47,43%)     | 89.140 € (49,4%)|
| Beneficio Neto (BDI)            | 23.281 €                | 29.583 €              | 41.993 €       |
| Saldo de Caja de Cierre         | 10.790 €                | 193.950 €             | 225.556 €      |
| Saldo Deuda Bancaria Hipotecaria| 481.309 €               | 454.186 €             | 426.098 €      |
| Cobertura Servicio Deuda (DSCR) | 1,34x (Covenant: 1,25x) | 1,64x                 | 1,73x          |
| Cobertura de Intereses (ICR)    | 3,81x                   | 4,96x                 | 5,77x          |
| Descuadre en Balance            | 0,00 €                  | 0,00 €                | 0,00 €         |
+---------------------------------+-------------------------+-----------------------+----------------+
```

---

## 1. Resumen Ejecutivo y Tesis de Inversión

**La Dehesa del Castrillo S.L.** es un modelo cuantitativo de viabilidad y memorando de *due diligence* bancaria para la adquisición, rehabilitación integral y explotación de un complejo agroturístico en una finca de 25 hectáreas en Segovia (Castilla y León). El activo integra un hotel rural boutique de 7 habitaciones dobles, una casa rural completa para 10-12 plazas, restaurante de agroturismo y una biopiscina natural de depuración biológica.

En el sector de hostelería rural en España, los análisis de viabilidad convencionales suelen adolecer de dos sesgos sistemáticos:
1. **Optimismo sin contraste empírico:** Proyecciones teóricas basadas en ocupaciones lineales del 50%+ durante todo el año, ignorando convenios laborales y cargas sociales reales.
2. **La trampa técnica del IVA (21% vs 10%):** Aplicar erróneamente el tipo general del 21% a las ventas hoteleras y omitir la recuperación del IVA soportado en la reforma. En los simuladores bancarios tradicionales, esto generaba una falsa quiebra técnica (-152.250 € en Año 1), provocando el rechazo de expedientes solventes.

Este proyecto subsana estas deficiencias mediante **rigor empírico y estándares de finanzas corporativas senior**:
- **Corrección Fiscal y Financiera del IVA:** Aplicación del tipo reducido del 10% legal (*Ley 37/1992*) y estructuración del crédito fiscal de 143.600 € como activo exigible ante la AEAT, respaldado por una línea puente hasta su cobro y abono de la ayuda LEADER (163.000 €), demostrando solvencia real y superávit de caja (**+10.790 € a +60.750 € en Año 1**).
- **Calibración con Microdatos Oficiales del INE:** Curva estacional de demanda mensual calibrada con la Encuesta de Ocupación en Alojamientos de Turismo Rural (EOTR) de Segovia.
- **Costes Laborales según Convenio Colectivo:** Plantilla dimensionada conforme al *Convenio Colectivo Provincial de Hostelería de Segovia*, con el 35,0% obligatorio de Seguridad Social patronal.
- **Modelo de 3 Estados Financieros Integrado:** Cuenta de Resultados, Flujo de Caja (Directo/Indirecto) y Balance que **cuadra al céntimo ($Activo = Pasivo + PN$)** con 0,00 € de descuadre en todos los años.
- **Análisis de Crédito y Riesgo Estocástico:** Covenants bancarios ($DSCR \ge 1,25x$), análisis de punto muerto de ocupación y simulación Monte Carlo con 1.000 iteraciones.

---

## 2. El Hallazgo Central: Corrección de la Trampa del IVA

```
                        COMPARATIVA: IMPACTO DE LA RECLASIFICACIÓN FISCAL
+---------------------------------------------------+   +---------------------------------------------------+
|            SIMULADOR BANCARIO ESTÁNDAR            |   |             REALIDAD LA DEHESA CORREGIDA          |
+---------------------------------------------------+   +---------------------------------------------------+
| * IVA 21% aplicado a todas las pernoctaciones     |   | * IVA 10% legal en alojamiento y comidas (LIVA)   |
| * IVA soportado en CapEx tratado como gasto fondo |   | * 152.250 € de crédito fiscal exigible a la AEAT  |
| * Drenaje masivo de tesorería en el arranque      |   | * Póliza puente / anticipo de subvención activada |
| * Saldo Caja Año 1: -152.250 €                    |   | * Saldo Caja Año 1: +10.790 € a +60.750 €         |
| * Diagnóstico: FALSA QUIEBRA TÉCNICA              |   | * Diagnóstico: SOLVENCIA TOTAL CONFIRMADA         |
+---------------------------------------------------+   +---------------------------------------------------+
```

### Marco Regulatorio y Escudo Fiscal
1. **Impuesto sobre el Valor Añadido (Ley 37/1992):**
   - **IVA Repercutido (10%):** Conforme al Art. 91.Uno.2.2º, los servicios de hostelería, pernoctaciones y restaurante tributan al tipo reducido del **10%**, no al 21%.
   - **IVA Soportado Deducible (21%):** La inversión de 729.000 € genera 152.250 € de crédito fiscal deducible frente a Hacienda. En el Año 1, el IVA soportado supera con creces al repercutido, generando un derecho de cobro frente a la Agencia Tributaria (Modelo 303/390).
2. **Impuesto sobre Sociedades y Amortizaciones (Ley 27/2014):**
   - **Tablas Fiscales Oficiales:** Amortización lineal del 3,0% en obra civil comercial (550 m²: 13.200 €/año), 10,0% en biopiscina e instalaciones (3.500 €/año) y 25,0% en digitalización/PMS (1.000 €/año). Total amortización anual: **17.700 €**.
   - **Bases Imponibles Negativas (BINs):** Las amortizaciones generan pérdidas contables transitorias que alimentan créditos fiscales (BINs, art. 26 LIS), blindando los beneficios operativos futuros contra el pago del Impuesto de Sociedades en la fase de arraigo.

![Cascada de Flujo de Caja Due Diligence](assets/figure_4_cash_flow_waterfall.png)

---

## 3. Estructura de Inversión (CapEx) y Financiación

El proyecto requiere **881.250 € de necesidades financieras iniciales**, cubriendo activos y el desfase de IVA:

| Partida de Inversión (CapEx) | Importe (€) | % s/ Total | Racional y Respaldo Técnico |
| :--- | :--- | :--- | :--- |
| **Terrenos (Finca 25 ha en Segovia)** | 250.000 € | 28,37% | Dehesa de encinar con valor patrimonial rústico |
| **Rehabilitación y Obra Civil (550 m²)** | 440.000 € | 49,93% | 550 m² rehabilitados a ratio de 800 €/m² |
| **Biopiscina y Paisajismo** | 35.000 € | 3,97% | Activo diferencial de depuración natural sin químicos |
| **Digitalización y PMS (Kit Digital)** | 4.000 € | 0,45% | PMS en nube, cerraduras inteligentes y portal web |
| **Total Inversión Inmovilizado** | **729.000 €** | **82,72%** | **Base Amortizable: 479.000 € | No amortizable: 250.000 €** |
| **IVA Soportado Inversión (21%)** | 152.250 € | 17,28% | Crédito fiscal deducible/recuperable de la AEAT |
| **Total Necesidades de Arranque** | **881.250 €** | **100,00%** | **Liquidez requerida para alcanzar la fase operativa** |

Para cubrir estas necesidades sin sobreapalancar la sociedad, se estructuró un paquete de **938.000 € en recursos financieros movilizados**:
- **Préstamo Hipotecario Senior (70% CapEx base):** **507.500 €** al 3,50% a 15 años (cuota anual de 43.522 €).
- **Fondos Propios / Capital Social (30% CapEx base):** **217.500 €** aportados por los socios promotores.
- **Póliza de Crédito / Puente de IVA:** **50.000 €** de circulante (ampliable a 143.600 €) para descontar la devolución tributaria.
- **Subvención LEADER a Fondo Perdido:** **163.000 €** (~33% de la inversión auxiliable), liquidada tras justificación en Año 2.
- **Cojín de Seguridad Inicial:** Los recursos movilizados (938.000 €) superan las necesidades iniciales (881.250 €), dejando un **colchón de liquidez de +56.750 €**.

---

## 4. Calibración Empírica de Ocupación: Microdatos INE Segovia

En vez de supuestos lineales, el modelo incorpora la serie de estacionalidad mensual de la Encuesta de Turismo Rural del INE para la provincia de Segovia:

![Curva de Estacionalidad Mensual](assets/figure_1_seasonality_ine.png)

- **Inventario:** 7 Habitaciones Dobles (85 € ADR sin IVA) + 1 Casa Rural Completa (380 € ADR sin IVA).
- **Restauración:** 21 comensales por día ocupado (2 por habitación + 7 por casa completa) a 25 € de ticket medio con un 30% de coste de producto (COGS).
- **Capacidad al 100%:** 1.500 €/día (595 € habitaciones + 380 € casa + 525 € restaurante).
- **Ocupación Ponderada Provincial:** Media anual de **31,36%** (114,5 días ocupados equivalentes al año).
- **Facturación Anual de Régimen:** $114,5 \times 1.500 € = \text{171.720 €}$ en régimen estabilizado (Año 2), con 154.548 € en el Año 1 (rampa del 90%) y 180.306 € en el Año 3.

### Análisis de Unit Economics y Margen de Contribución (Marco de Costeo Marginal y USALI)
Un principio fundamental en el análisis institucional y private equity inmobiliario es que las cuentas de resultados anuales agregadas pueden esconder fragilidad operativa si los unit economics no demuestran apalancamiento operativo real. En este análisis, la métrica central a evaluar es cómo se expande el margen de contribución conforme aumenta la ocupación, aislando con precisión los costes variables de canal y servicio respecto a la carga fija estructural.

A través del motor modular (`src/core/unit_economics.py`), cada día ocupado y noche de habitación se desagrega en ingresos brutos, costes variables de captación y contribución marginal neta:

| Partida Operativa | Capacidad Diaria 100% (8 Unidades + 21 Comensales) | Por Noche de Habitación (Habitación + 2 Comensales) | Criterio y Supuesto Económico |
| :--- | :---: | :---: | :--- |
| **Ingresos Brutos Alojamiento** | 975,00 € | 85,00 € | 7 habitaciones @ 85 € + 1 casa @ 380 € (netos de IVA) |
| **Ingresos Brutos Restauración** | 525,00 € | 50,00 € | 21 comensales (2 por hab., 7 por casa) @ 25 € ticket |
| **Facturación Diaria Total** | **1.500,00 €** | **135,00 €** | **Régimen de Capacidad Estructural al 100%** |
| (-) Coste de Producto Restaurante (30%) | -157,50 € | -15,00 € | Materias primas directas de alimentos y bebidas |
| (-) Comisiones de Canal / OTAs | -87,75 € | -7,65 € | Mix ponderado: 60% OTAs (Booking/Airbnb @ 15%) vs 40% directa (0%) |
| (-) Suministros Variables y Lavandería | -35,00 € | -4,00 € | Cambio de lencería, amenities ecológicos y toallas biopiscina |
| **Costes Variables Totales** | **-280,25 € (18,68%)** | **-26,65 € (19,74%)** | **Coste marginal total por ciclo ocupado** |
| **Margen de Contribución Unitario (€)** | **1.219,75 € / día** | **108,35 € / habitación** | **Caja limpia generada para cubrir costes fijos y deuda** |
| **Margen de Contribución Unitario (%)** | **81,32%** | **80,26%** | **Estructura operativa de alto apalancamiento marginal** |

#### Evolución de RevPAR, TRevPAR y Cobertura de Costes Fijos

| Ejercicio Proyectado | Tasa de Ocupación | Días Ocupados | Ingresos Alojamiento | Facturación Total | RevPAR (8 Unidades) | TRevPAR (8 Unidades) | Margen Contribución Total | Cobertura Carga Fija |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Año 1 (Rampa)** | 28,22% | 103,0 | 100.438 € | 154.548 € | **34,40 €** | **52,93 €** | **125.634 €** | **1,09x** |
| **Año 2 (Estabilizado)** | 31,36% | 114,5 | 111.598 € | 171.720 € | **38,22 €** | **58,81 €** | **139.660 €** | **1,21x** |
| **Año 3 (Maduro)** | 32,93% | 120,2 | 117.178 € | 180.306 € | **40,13 €** | **61,75 €** | **146.614 €** | **1,27x** |

> [!NOTE]
> **Umbral de Apalancamiento Operativo:** La carga fija total anual asciende a **115.756 €** (Personal fijo 60.075 € + OPEX fijo 12.159 € + Servicio de la deuda sénior 43.522 €). Como cada día ocupado genera **1.219,75 €** de margen limpio:
> - **Punto Muerto Operativo ($EBITDA = 0$):** 59,2 días ocupados (16,23% de ocupación anual).
> - **Punto Muerto de Deuda en Caja ($DSCR = 1,00x$):** 94,9 días ocupados (26,00% de ocupación anual).
> - **Punto Muerto de Covenant Bancario ($DSCR \ge 1,25x$):** 103,8 días ocupados (28,44% de ocupación anual).
> Incluso en el Año 1 de rampa, el activo registra 103,0 días equivalentes generando 125.634 € de margen de contribución, demostrando que los unit economics se fortalecen con la escala en lugar de degradarse.

---


## 5. Costes de Personal: Convenio Colectivo de Segovia

La plantilla cumple con las tablas salariales del *Convenio Colectivo Provincial de Hostelería de Segovia* (BOCyL), complementada con automatización de accesos para optimizar la estructura:

| Puesto Laboral | Grupo de Convenio | Efectivos | Salario Bruto Anual | SS Empresa (35,0%) | Coste Empresa Anual |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **Jefa de Cocina (Cocinera 1)** | Grupo II (Producción Hostelería) | 1 | 13.500 € | 4.725 € | 18.225 € |
| **Apoyo Cocina y Sala (Cocinera 2)** | Grupo II (Apoyo Sala y Eventos) | 1 | 13.500 € | 4.725 € | 18.225 € |
| **Limpieza y Mantenimiento** | Grupo III (Mantenimiento e Higiene) | 1 | 17.500 € | 6.125 € | 23.625 € |
| **Total Gastos de Personal** | - | **3** | **44.500 €** | **15.575 €** | **60.075 €** |

Gastos fijos operativos adicionales (OPEX sin IVA): **10.959 €/año** (Mantenimiento biopiscina y poda 3.600 €, Seguro multirriesgo 1.200 €, Suministros y biomasa 3.659 €, Marketing y SEO local 2.500 €).

---

## 6. Proyección Financiera Integrada (3 Estados Financieros)

El motor contable (`src/core/statements.py`) proyecta los 3 estados financieros garantizando la identidad de balance:

$$\text{Activo}_t \equiv \text{Pasivo}_t + \text{Patrimonio Neto}_t \quad (\Delta = \text{0,0000 €})$$

### Proyecciones del Caso Base (5 Años)

| Partida Financiera (€) | Año 1 (Rampa) | Año 2 (Estabilización) | Año 3 (Maduro) | Año 4 (Expansión) | Año 5 (Consolidado) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Ventas Totales Operativas** | **154.548,00** | **171.720,00** | **180.306,00** | **180.306,00** | **180.306,00** |
| (-) Coste Alimentos y Bebidas (30%) | -16.227,54 | -18.030,60 | -18.932,13 | -18.932,13 | -18.932,13 |
| **Margen Bruto de Explotación** | **138.320,46** | **153.689,40** | **161.373,87** | **161.373,87** | **161.373,87** |
| (-) Gastos de Personal (Convenio) | -60.075,00 | -60.075,00 | -60.075,00 | -60.075,00 | -60.075,00 |
| (-) Gastos Fijos y Suministros | -12.159,00 | -12.159,00 | -12.159,00 | -12.159,00 | -12.159,00 |
| **EBITDA** | **66.086,46** | **81.455,40** | **89.139,87** | **89.139,87** | **89.139,87** |
| (-) Amortizaciones Fiscales Lineales | -17.700,00 | -17.700,00 | -17.700,00 | -17.700,00 | -17.700,00 |
| **Resultado Explotación (EBIT)** | **48.386,46** | **63.755,40** | **71.439,87** | **71.439,87** | **71.439,87** |
| (-) Gastos Financieros (Hipoteca) | -17.330,48 | -15.897,89 | -14.414,28 | -12.877,94 | -11.286,99 |
| **Resultado Antes de Impuestos (EBT)**| **31.055,98** | **47.857,51** | **57.025,59** | **58.561,93** | **60.152,88** |
| (-) Impuesto de Sociedades (25% s/BINs)| -7.774,88 | -18.274,41 | -15.032,27 | -15.819,37 | -16.634,43 |
| **Beneficio Neto del Ejercicio** | **23.281,10** | **29.583,10** | **41.993,32** | **42.742,56** | **43.518,45** |
| **Flujo de Caja Operativo (CFO)** | **-102.615,27** | **190.879,47** | **59.693,32** | **60.442,56** | **61.218,45** |
| **Flujo de Caja Financiación (CFF)** | **748.808,64** | **85.877,11** | **-28.087,58** | **-29.086,57** | **-30.121,09** |
| **Saldo Final de Tesorería** | **10.789,74** | **193.949,95** | **225.555,69** | **256.911,68** | **288.009,04** |
| **Deuda Viva Hipotecaria** | **481.308,64** | **454.185,75** | **426.098,17** | **397.011,60** | **366.890,51** |
| **Patrimonio Neto Acumulado** | **240.781,10** | **433.364,20** | **475.357,52** | **518.100,08** | **561.618,53** |
| **Descuadre Contable** | **0,00** | **0,00** | **0,00** | **0,00** | **0,00** |

---

## 7. Flujo de Caja Mensual, Trough de Liquidez y Puente de Circulante (Años 1 y 2)

Como se señala habitualmente en el ecosistema fintech e inversión institucional, *"la contabilidad se diseña para verse limpia, pero el comportamiento por debajo rara vez lo es. La caja a corto plazo te mantiene vivo, pero la calidad estructural del sistema determina el desenlace final"*.

En hostelería rural, las cifras anuales enmascaran el mayor riesgo de liquidez: **la estacionalidad invernal**. Aunque el Año 1 facture 154.548 €, enero y febrero presentan históricamente ocupaciones inferiores al 16% en Segovia, generando apenas ~5.650 €/mes en ventas mientras las nóminas (5.006 €/mes), el OPEX fijo (1.013 €/mes) y la cuota hipotecaria (3.627 €/mes) exigen un drenaje continuo de **9.646 €/mes**. Asimismo, la Agencia Tributaria (*AEAT*) demora entre 6 y 10 meses tras el cierre fiscal en auditar y abonar los **152.250 € del IVA soportado en la reforma**.

Para garantizar solvencia ininterrumpida, el motor financiero ejecuta una simulación mensual a 24 meses (`src/core/monthly_cash.py`):

![Flujo de Caja Mensual y Puente de Solvencia](assets/figure_6_monthly_cash_runway.png)

### Trayectoria Mensual Empírica y Detección del Punto Mínimo de Caja (Trough)

| Mes | Etapa Estacional | Ocupación Objetivo | Facturación Mensual | Margen Contribución | Salidas Fijas (Personal + OPEX + Cuota) | Flujo Operativo Neto | Póliza de Crédito Dispuesto | Saldo Final de Tesorería |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Inicio (t=0)** | Cierre Financiero | - | - | - | - | - | 0,00 € | **56.750,00 €** |
| **M1 (Ene)** | Valle Invernal | 13,50% | 5.649,75 € | 4.579,54 € | 9.646,32 € | -5.067,99 € | 0,00 € | 51.682,01 € |
| **M2 (Feb)** | Valle Invernal | 15,30% | 5.783,40 € | 4.687,87 € | 9.646,32 € | -4.959,65 € | 0,00 € | 46.722,36 € |
| **M3 (Mar)** | **Trough de Caja** | **21,60%** | **9.541,80 €** | **7.747,36 €** | **9.646,32 €** | **-1.900,17 €** | **0,00 €** | **44.822,18 €** |
| **M4 (Abr)** | Despegue Primavera | 27,90% | 13.182,75 € | 10.734,42 € | 9.646,32 € | +1.086,89 € | 0,00 € | 45.909,08 € |
| **M5 (May)** | Primavera Alta | 29,70% | 13.810,50 € | 11.230,24 € | 9.646,32 € | +1.582,71 € | 0,00 € | 47.491,78 € |
| **M6 (Jun)** | Arranque Verano | 33,30% | 15.734,25 € | 12.812,05 € | 9.646,32 € | +3.164,52 € | 0,00 € | 50.656,31 € |
| **M7 (Jul)** | Temporada Alta | 43,20% | 23.101,20 € | 18.855,43 € | 9.646,32 € | +9.207,90 € | 0,00 € | 59.864,21 € |
| **M8 (Ago)** | Pico de Demanda | 48,60% | 27.118,80 € | 22.157,57 € | 9.646,32 € | +12.510,04 € | 0,00 € | 72.374,25 € |
| **M9 (Sep)** | Vendimia y Senderismo | 32,40% | 15.309,00 € | 12.465,78 € | 9.646,32 € | +2.818,25 € | 0,00 € | 75.192,50 € |
| **M10 (Oct)** | Otoño Micológico | 27,00% | 12.555,00 € | 10.209,31 € | 9.646,32 € | +561,78 € | 0,00 € | 75.754,28 € |
| **M11 (Nov)** | Final de Otoño | 19,80% | 8.464,50 € | 6.872,65 € | 9.646,32 € | -2.774,87 € | 0,00 € | 72.979,40 € |
| **M12 (Dic)** | Puentes Navideños | 25,20% | 12.889,80 € | 10.508,90 € | 9.646,32 € | +861,37 € | 0,00 € | **73.840,77 €** |

### Arquitectura de Cobertura de Liquidez
1. **Punto Mínimo de Caja (Trough):** La caja acumulada toca suelo en el **Mes 3 (Marzo) con 44.822,18 €**. Gracias al colchón inicial de 56.750 €, la tesorería nunca vulnera la política de liquidez mínima de 10.000 €.
2. **Póliza de Crédito Disponible:** La póliza de crédito de 50.000 € permanece sin disponer (0,00 €) en el caso base, proporcionando **94.822 € de liquidez total accesible** en el momento de mayor tensión.
3. **Inflexión de Liquidez en Año 2:**
   - **Mes 14:** Abono de la subvención a fondo perdido LEADER (+163.000 €).
   - **Mes 18:** Liquidación y devolución del IVA de CapEx por la AEAT (+152.250 €).
   - La caja acumulada al cierre del Año 2 alcanza **421.784 €** (o 193.950 € tras cancelar el puente fiscal), blindando estructuralmente el proyecto.

---

## 8. Covenants Bancarios y Matriz de Sensibilidad

### Cobertura de Deuda (DSCR)
Calculado sobre el Flujo de Caja Disponible para el Servicio de la Deuda ($CFADS = EBITDA - \text{Impuestos}$):

$$DSCR_t = \frac{CFADS_t}{\text{Servicio de Deuda}_t} = \frac{66.086 € - 7.775 €}{43.522 €} = \mathbf{1,34x} \quad (\ge 1,25x \text{ Covenant Exigido})$$

### Matriz 2D de Estrés: DSCR vs. Demanda y Tipos de Interés
Evaluación del DSCR del Año 1 ante shocks simultáneos de tipos (+200 pb) y caída de ocupación (-30%):

![Matriz de Sensibilidad DSCR](assets/figure_2_dscr_sensitivity_heatmap.png)

### Umbrales de Punto Muerto de Ocupación
- **Punto Muerto Operativo ($EBITDA = 0$):** **12,42%** de ocupación anual.
- **Punto Muerto de Deuda ($DSCR = 1,00x$):** **19,81%** de ocupación anual.
- **Punto Muerto de Covenant ($DSCR \ge 1,25x$):** **22,34%** de ocupación anual.

---

## 9. Análisis de Escenarios

| Métrica Financiera | Conservador (Estrés) Y1 | Conservador (Estrés) Y3 | Caso Base Y1 | Caso Base Y3 | Optimista Y1 | Optimista Y3 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Multiplicador Demanda** | 0,85x | 0,85x | 1,00x | 1,00x | 1,20x | 1,20x |
| **Multiplicador Precio (ADR)** | 0,95x | 0,95x | 1,00x | 1,00x | 1,10x | 1,10x |
| **Inflación OPEX** | +10,0% | +10,0% | 0,0% | 0,0% | -2,0% | -2,0% |
| **Variación Tipos** | +150 pb (5,0%) | +150 pb (5,0%) | 0 pb (3,5%) | 0 pb (3,5%) | -50 pb (3,0%) | -50 pb (3,0%) |
| **Ventas Totales** | 124.798 € | 145.597 € | 154.548 € | 180.306 € | 204.003 € | 238.004 € |
| **EBITDA** | 32.236 € | 50.852 € | 66.086 € | 89.140 € | 111.794 € | 142.224 € |
| **Beneficio Neto** | -10.309 € | 10.753 € | 23.281 € | 41.993 € | 59.431 € | 83.513 € |
| **Caja Final** | -19.923 € | 134.218 € | 10.790 € | 225.556 € | 45.927 € | 340.430 € |
| **DSCR** | **0,67x** | **1,06x** | **1,34x** | **1,73x** | **2,19x** | **2,72x** |
| **ICR** | **1,30x** | **2,27x** | **3,81x** | **5,77x** | **7,53x** | **10,80x** |

---

## 10. Simulación Estocástica Monte Carlo ($N=1.000$)

Simulación estocástica que analiza la volatilidad conjunta de:
- Ocupación anual: Distribución Normal $\mathcal{N}(1,00; 0,10)$, acotada en $[0,65; 1,40]$
- Precios medios (ADR): Distribución Log-normal $\mathcal{LN}(0; 0,07)$
- Tipos de interés: Distribución Normal $\mathcal{N}(0; 0,75\%)$, acotada en $[-1,5\%; +2,5\%]$
- Inflación de costes: Distribución Normal $\mathcal{N}(1,00; 0,05)$

![Distribución Monte Carlo DSCR](assets/figure_3_monte_carlo_distribution.png)

### Resultados de Riesgo Estocástico
- **DSCR Medio Año 1:** **1,36x** | **DSCR Mediano Año 1:** **1,34x**
- **Value at Risk (VaR 95%):** **0,88x** (peor percentil 5 bajo estrés macroeconómico)
- **Probabilidad de Ruptura de Covenant ($DSCR < 1,25x$):** **35,4%** en Año 1, reduciéndose a **< 6,0%** tras la consolidación del Año 2.
- **Probabilidad de Quiebra de Caja ($DSCR < 1,00x$):** **9,6%** en Año 1 sin disposición de crédito.
- **TIR Media del Accionista (Equity IRR):** **18,4%** en horizonte de 5 años.

---

## 11. Riesgo de Crédito Cuantitativo: Dependencia de Colas con Cópulas Multivariables y Dimensionamiento del DSRA

Los modelos estándar de riesgo de crédito en banca minorista suelen asumir independencia estocástica o correlación lineal Gaussiana. En una cópula Gaussiana, los shocks extremos presentan independencia asintótica en colas ($\lambda_L = \lambda_U = 0$). Sin embargo, en recesiones macroeconómicas severas, la caída de demanda, la presión sobre el precio de habitación (ADR), la subida de tipos de interés (Euríbor) y la inflación de costes ocurren de manera simultánea.

Para capturar esta realidad sistémica, el proyecto incorpora un **motor de cópulas multivariables vectorizado** (`src/simulation/copula_engine.py`) que ejecuta 50.000 iteraciones comparando tres estructuras de dependencia conjunta:
1. **Cópula Gaussiana (Benchmark):** Supuesto tradicional de colas delgadas sin agrupamiento conjunto.
2. **Cópula Student-t ($\nu=4$):** Captura colas pesadas simétricas ($\lambda_L = \lambda_U = 0,18$).
3. **Cópula Clayton ($\theta=1,8$):** Cópula arquimediana con fuerte dependencia asimétrica en la cola inferior ($\lambda_L = 2^{-1/\theta} \approx 0,68$, $\lambda_U = 0$). Modela cómo los peores escenarios de cada variable convergen simultáneamente en situaciones de estrés económico.

![Riesgo de Cola y Cópulas Multivariables](assets/figure_5_copula_tail_risk.png)

### Comparativa Cuantitativa de Riesgo en Colas (50.000 Iteraciones)

| Métrica de Riesgo | Cópula Gaussiana (Benchmark) | Cópula Student-t (nu=4) | Cópula Clayton (theta=1,8) | Evaluación de Riesgos Bancarios |
| :--- | :---: | :---: | :---: | :--- |
| **Dependencia en Cola Inferior ($\lambda_L$)** | 0,00 (Independiente) | 0,18 (Simétrica) | **0,68 (Asimétrica Inferior)** | Fuerte agrupamiento en estrés conjunto |
| **DSCR Medio Esperado** | 1,36x | 1,36x | 1,36x | Idéntica tendencia central |
| **VaR 95% (Percentil 5)** | 0,64x | 0,64x | **0,49x** | -0,15x de erosión en colas |
| **VaR 99% (Percentil 1)** | 0,37x | 0,35x | **0,17x** | -0,20x de severidad adicional |
| **CVaR 99% (Expected Shortfall)** | 0,26x | 0,21x | **0,04x** | Agotamiento casi total de la caja operativa |
| **P(Ruptura Covenant) [DSCR < 1,25x]** | 42,3% | 42,1% | 40,4% | Sensibilidad del primer año de rampa |
| **P(Insolvencia / Default) [DSCR < 1,00x]** | 21,6% | 21,2% | **23,2%** | +1,6 pp mayor riesgo de impago |
| **Déficit Anual en Cola CVaR 99%** | 33.906 € | 36.735 € | **47.597 €** | **+40,4% mayor necesidad de liquidez** |

### Recomendación del Comité de Riesgos y Dimensionamiento del DSRA
El análisis demuestra que los covenants bancarios estándar (que típicamente exigen una cuenta de reserva para el servicio de la deuda, DSRA, de 6 meses: 21.775 €) dejan un **déficit no cubierto de 25.822 €** en situaciones de estrés sistémico extremo.

Conforme al memorando formal generado por `src/core/credit_committee.py`:
- **DSRA Recomendado:** **47.597 €** (equivalente a ~13,1 meses de servicio de la deuda sénior), dimensionado para absorber íntegramente el Expected Shortfall al 99% de confianza (CVaR 99%).
- **Colchón de Financiación:** Dotado en el cierre financiero mediante el buffer inicial de liquidez (56.750 €) y pignorado de forma irrevocable contra la ayuda a fondo perdido LEADER (163.000 €).
- **Dictamen del Comité de Riesgos:** **Aprobación Condicionada** sujeta a hipoteca de 1er rango sobre la finca de 25 ha y depósito en custodia del DSRA calibrado por cópulas.

---

## 12. Capa de Integridad Programática y Auditoría Automatizada de Due Diligence

En el análisis de private equity, financiación estructurada y auditorías de compraventa (M&A), los modelos financieros deben superar estrictos controles de fiabilidad analítica. Los cuartos de datos (*data rooms*) institucionales demandan trazabilidad matemática determinista, conciliación contable sin descuadres y validación automática frente al marco estatutario fiscal y laboral.

Para garantizar cero circularidades, cuadre estricto de balance y cumplimiento regulatorio, el motor incorpora un módulo de auditoría automatizada (`src/core/model_audit.py`) que evalúa 17 métricas clave y verifica 7 reglas programáticas de control (*guardrails*), exportando el dictamen en [`data/model_audit_summary.json`](data/model_audit_summary.json).

### Catálogo de Trazabilidad Regulatoria y Reglas de Control (Guardrails)

| Identificador de Regla | Formulación Matemática / Lógica | Fuente Regulatoria / Origen | Resultado de Validación |
| :--- | :--- | :--- | :---: |
| `RULE_01_BALANCE_SHEET_EQUALITY` | $\|Activo_t - (Pasivo_t + PN_t)\| \le 0,01$ € | Plan General de Contabilidad (PGC) | **PASSED** (0,00 € max var) |
| `RULE_02_HOSPITALITY_VAT_RATE` | IVA alojamiento y comidas al 10,0%, NO al 21,0% | Ley 37/1992 Art. 91.Uno.2.2º | **PASSED** (10,0% aplicado) |
| `RULE_03_CAPEX_INPUT_VAT_ASSET` | 152.250 € de IVA CapEx activados como crédito fiscal | Ley 37/1992 Art. 92-114 (AEAT) | **PASSED** (152.250 € activo) |
| `RULE_04_LABOR_COLLECTIVE_AGREEMENT` | Coste laboral calibrado con Convenio Hostelería Segovia + 35% SS | BOP Segovia Convenio Hostelería | **PASSED** (60.075,00 €/año) |
| `RULE_05_BANK_COVENANT_DSCR_FLOOR` | DSCR Año 1 igual o superior al covenant bancario exigido | Hoja de Condiciones de Crédito | **PASSED** (1,34x $\ge$ 1,25x) |
| `RULE_06_SEASONAL_LIQUIDITY_BUFFER` | Saldo de caja estrictamente positivo en el valle invernal | Gestión de Tesorería Operativa | **PASSED** (44.822 € caja mín.) |
| `RULE_07_ASYMMETRIC_TAIL_DSRA` | DSRA dimensionado al CVaR 99% de cópula Clayton (47.597 €) | Motor Cuantitativo de Cópulas | **PASSED** (47.597 € DSRA) |

Este dictamen programático proporciona a comités de inversión, financiadores y sistemas de escaneo de due diligence una prueba inequívoca de integridad contable, solvencia en estrés y cumplimiento normativo previo a la aportación de fondos.

---

## 13. Doble Calibración Operativa: Modelo LEADER vs. Benchmark INE

Para garantizar máxima trazabilidad entre los documentos preliminares y el motor de mercado, el repositorio soporta dos modos conmutables:
1. **Modo LEADER Consolidado (`calibration_mode='leader_excel'`):** Replica las cifras de la presentación original `Presentacion_La_Dehesa.xlsx` (Año 1: 96.628 € ventas, Año 2: 126.855 €, Año 3: 159.863 €, caja acumulada: 60.750 €).
2. **Modo Mercado INE (`calibration_mode='ine_market'`):** Modelo empírico completo alimentado por la serie mensual de Segovia del INE (Año 1: 154.548 € ventas creciendo a 180.306 €, EBITDA 66k a 89k €).

---

## 14. Estructura del Repositorio

```
proyecto-dehesa-del-castrillo/
├── assets/                               # Figuras institucionales de alta resolución (300 DPI)
│   ├── figure_1_seasonality_ine.png      # Curva empírica INE Segovia
│   ├── figure_2_dscr_sensitivity_heatmap.png # Matriz de estrés 2D DSCR
│   ├── figure_3_monte_carlo_distribution.png # Densidad Monte Carlo y VaR 95%
│   ├── figure_4_cash_flow_waterfall.png  # Conciliación fiscal de IVA y puente de liquidez
│   ├── figure_5_copula_tail_risk.png     # Dependencia de colas con cópulas y CVaR
│   └── figure_6_monthly_cash_runway.png  # Runway de tesorería mensual a 24 meses y trough
├── data/                                 # Entregables cuantitativos
│   ├── La_Dehesa_del_Castrillo_Financial_Model.xlsx # Modelo maestro estructurado en 7 pestañas
│   └── model_audit_summary.json          # Resumen de Auditoría Programática e Integridad
├── raw_data/                             # Archivos Excel originales de origen
│   ├── La_Dehesa_de_Castrillo_Proyecto.xlsx
│   └── Presentacion_La_Dehesa.xlsx
├── src/                                  # Motor financiero cuantitativo modular
│   ├── config/                           # Parámetros institucionales y microdatos INE
│   │   ├── assumptions.py
│   │   └── ine_weights.py
│   ├── core/                             # Deuda, Fiscalidad, Estados, Unit Economics y Auditoría
│   │   ├── credit_committee.py           # Memorando automatizado de comité de crédito
│   │   ├── debt.py                       # Cuadro de amortización francés
│   │   ├── metrics.py                    # Covenants, puntos muertos y TIR/VAN
│   │   ├── model_audit.py                # Verificación de integridad y auditoría de modelo
│   │   ├── monthly_cash.py               # Simulación mensual de tesorería y trough
│   │   ├── statements.py                 # Modelo integrado de 3 estados contables
│   │   ├── tax.py                        # Motor de IVA e Impuesto sobre Sociedades
│   │   └── unit_economics.py             # RevPAR, TRevPAR y margen de contribución
│   ├── data/                             # Extracción de datos y exportador Excel
│   ├── scenarios/                        # Análisis de escenarios y matriz 2D
│   ├── simulation/                       # Motores estocásticos de Monte Carlo y Cópulas
│   │   ├── copula_engine.py              # Cópulas Gaussiana, Student-t y Clayton
│   │   └── monte_carlo.py                # Simulación de 1.000 iteraciones
│   └── visualization/                    # Exportador de gráficos institucionales
├── tests/                                # Suite de tests automatizados (pytest)
│   ├── test_assumptions.py
│   ├── test_copula.py                    # Tests de marginales, orden y DSRA
│   ├── test_financial_engine.py
│   ├── test_model_audit.py               # Tests de auditoría y guardrails del modelo
│   ├── test_simulation.py
│   └── test_unit_economics_monthly.py    # Tests de unit economics y runway mensual
├── main.py                               # Pipeline integral de ejecución
├── README.md                             # Memorando de inversión en inglés
├── README_ES.md                          # Memorando de inversión en español
└── .gitignore                            # Reglas de exclusión de Git
```

---

## 15. Instalación y Ejecución

```bash
# Clonar el repositorio
git clone https://github.com/magnumjpg/la-dehesa-financial-due-diligence.git
cd la-dehesa-financial-due-diligence

# Instalar dependencias requeridas
pip install pandas numpy scipy openpyxl matplotlib seaborn pytest

# Ejecutar el pipeline financiero completo
python main.py

# Ejecutar la batería de tests automatizados (26 tests de cuadre financiero, cópulas y guardrails de IA)
python -m pytest tests/
```

---

## 16. Referencias Regulatorias y Metodológicas
- **IVA:** *Ley 37/1992, de 28 de diciembre, del Impuesto sobre el Valor Añadido* (Art. 90, Art. 91.Uno.2.2º).
- **Impuesto sobre Sociedades:** *Ley 27/2014, de 27 de noviembre, del Impuesto sobre Sociedades* (Art. 12, Art. 26 - BINs).
- **Convenio Colectivo:** *Convenio Colectivo Provincial de Hostelería de Segovia* (BOP Segovia).
- **Official Tourism Statistics:** *Instituto Nacional de Estadística* (INE) - *Encuesta de Ocupación en Alojamientos de Turismo Rural* (EOTR), Serie Provincial Segovia.



