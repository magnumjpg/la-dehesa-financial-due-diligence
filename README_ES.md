# La Dehesa del Castrillo S.L.
### Viabilidad Financiera, Due Diligence Operativa y Stress-Testing Estocástico para Hostelería Rural

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests: Pytest Passed](https://img.shields.io/badge/tests-16%20passed-brightgreen.svg)](https://docs.pytest.org/)
[![Deliverable: Excel Model](https://img.shields.io/badge/Modelo%20Excel-5%20Pestañas%20.XLSX-success.svg)](data/La_Dehesa_del_Castrillo_Financial_Model.xlsx)

[English](README.md) | [Español](README_ES.md)

**Autor:** Jaime Pérez  
**Especialidad:** Real Estate Private Equity, Due Diligence Operativa y Análisis de Crédito Bancario  
**Alcance del Proyecto:** Finca Rural de 25 Hectáreas | Segovia, España | Inversión: 729.000 € | Financiación 70/30 Deuda/Capital  
**Entregables Principales:** Motor Financiero Modular en Python (`/src`), Figuras Institucionales de Alta Resolución (`/assets`), Batería de Tests Unitarios (`/tests`) y Modelo Financiero Multicapa en Excel (`data/La_Dehesa_del_Castrillo_Financial_Model.xlsx`).

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

## 7. Covenants Bancarios y Matriz de Sensibilidad

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

## 8. Análisis de Escenarios

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

## 9. Simulación Estocástica Monte Carlo ($N=1.000$)

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

## 10. Doble Calibración Operativa: Modelo LEADER vs. Benchmark INE

Para garantizar máxima trazabilidad entre los documentos preliminares y el motor de mercado, el repositorio soporta dos modos conmutables:
1. **Modo LEADER Consolidado (`calibration_mode='leader_excel'`):** Replica las cifras de la presentación original `Presentacion_La_Dehesa.xlsx` (Año 1: 96.628 € ventas, Año 2: 126.855 €, Año 3: 159.863 €, caja acumulada: 60.750 €).
2. **Modo Mercado INE (`calibration_mode='ine_market'`):** Modelo empírico completo alimentado por la serie mensual de Segovia del INE (Año 1: 154.548 € ventas creciendo a 180.306 €, EBITDA 66k a 89k €).

---

## 11. Estructura del Repositorio y Ejecución

```bash
# Clonar el repositorio
git clone https://github.com/magnumjpg/hospitality-credit-underwriting-model.git
cd hospitality-credit-underwriting-model

# Instalar dependencias requeridas
pip install pandas numpy openpyxl matplotlib seaborn pytest

# Ejecutar el pipeline financiero completo
python main.py

# Ejecutar la batería de tests automatizados (16 tests de cuadre financiero)
python -m pytest tests/
```

---

## 12. Referencias Regulatorias y Metodológicas
- **IVA:** *Ley 37/1992, de 28 de diciembre, del Impuesto sobre el Valor Añadido* (Art. 90, Art. 91.Uno.2.2º).
- **Impuesto sobre Sociedades:** *Ley 27/2014, de 27 de noviembre, del Impuesto sobre Sociedades* (Art. 12, Art. 26 - BINs).
- **Convenio Colectivo:** *Convenio Colectivo Provincial de Hostelería de Segovia* (BOP Segovia).
- **Estadísticas de Turismo:** *Instituto Nacional de Estadística* (INE) - *Encuesta de Ocupación en Alojamientos de Turismo Rural* (EOTR), Serie Provincial Segovia.

---

## Autor
**Jaime Pérez**  
*Real Estate Private Equity | Quantitative Financial Modeling | Corporate Credit Analysis*  
GitHub Portfolio: [github.com/magnumjpg](https://github.com/magnumjpg)
