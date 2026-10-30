# La Dehesa del Castrillo S.L.

*Viabilidad hotelera, underwriting de deuda senior y auditoría financiera computada.*

[![CI](https://github.com/magnumjpg/la-dehesa-financial-due-diligence/actions/workflows/tests.yml/badge.svg)](https://github.com/magnumjpg/la-dehesa-financial-due-diligence/actions/workflows/tests.yml) [![tests](https://img.shields.io/badge/tests-121%20passed-brightgreen)](https://github.com/magnumjpg/la-dehesa-financial-due-diligence/actions/workflows/tests.yml) [![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/) [![License](https://img.shields.io/badge/license-MIT-green)](LICENSE) [![Data](https://img.shields.io/badge/data-promoter%20workbook%20%2B%20INE-informational)](MODEL_GOVERNANCE_ES.md)

**Español** · [English](README.md) · [Gobernanza del modelo](MODEL_GOVERNANCE_ES.md) · [Modelo en Excel](data/La_Dehesa_del_Castrillo_Financial_Model.xlsx)

> **Resumen ejecutivo**: Due diligence financiera y evaluación independiente de riesgo crediticio para un activo hotelero rural de 25 hectáreas en Segovia, España. Evalúa la capacidad de servicio de la deuda bajo amortización completa, identifica la rotura del covenant financiero y modeliza escenarios de reestructuración operativa.

**Entregables y estándares:** Motor financiero en Python 3.11 · suite de 121 tests unitarios (`pytest`) · auditoría computada de 16 reglas · modelo dinámico en Excel de 22 pestañas · estructura compatible con USALI.

---

## 1. Resumen ejecutivo y veredicto de crédito

| Métrica | Plan del Promotor (Deck) | Auditoría Institucional (Caso Gestión) | Impacto Crediticio / Variación |
| :--- | :--- | :--- | :--- |
| **CapEx Total del Proyecto** | 725.000 € | **1.050.100 €** | +325.100 € (+44,8% sobrecoste real) |
| **Equity Requerido en Caja** | 217.500 € (30,0%) | **521.090 € (49,6%)** | +303.590 € (+139,6% de fondos propios) |
| **Línea de Deuda Senior** | 367.535 € (35,0% LTV) | **367.535 € (Solicitada)** | Capacidad máxima topada en **339.145 €** |
| **DSCR Año 2 (Con amortización)** | No modelizado (>2,0x afirmado) | **1,15x** | **FALLA** (Rompe covenant bancario de 1,25x) |
| **DSCR Mínimo en el periodo** | 2,10x (declarado) | **1,15x** | No recupera el 1,25x en los primeros 5 años |
| **TIR del Proyecto (Exit 8,5%)** | +6,84% | **-9,49%** | Rentabilidad económica negativa vs WACC 8,0% |
| **Recomendación de Comité** | Aprobar financiación | **RECHAZAR EN ESTRUCTURA ACTUAL** | Activo sobreapalancado; requiere rediseño |

El 2,10x de la columna del promotor es la cifra declarada en el deck. El caso del promotor auditado alcanza un DSCR mínimo de 0,33x (sección 2), mientras que el 1,15x de esta tabla corresponde al caso de gestión.

### Veredicto del comité de riesgos: rechazar en su estructura actual
La recomendación de underwriting es **DENEGAR LA OPERACIÓN TAL Y COMO ESTÁ PLANTEADA**. Aunque el proyecto cumple formalmente con el límite de Loan-to-Value (35,0% LTV sobre una tasación de 1,05 M€), la operación está estrangulada por el flujo de caja operativo disponible para la deuda (CFADS):

1. **CapEx Infradimensionado**: El presupuesto inicial del promotor omitió partidas críticas: cocina industrial (55k €), FF&E y equipamiento (65k €), honorarios facultativos (42,6k €), costes preoperativos (35k €) y contingencias del 5% (35,5k €). El CapEx real de obra son 800.100 € (1.050.100 € sumando los 250k € de la finca aportada en especie).
2. **Déficit de Fondos Propios**: Cuadrar los orígenes y aplicaciones al cierre financiero requiere **521.090 € de equity en efectivo** (49,6% del CapEx), además de una póliza puente de IVA de 168k €. El 30% propuesto por el promotor dejaba un agujero de liquidez inmediato de más de 303k €.
3. **Incumplimiento de Covenant en Año 2**: El Año 1 supera la prueba gracias a los 12 meses de carencia de principal (DSCR de 1,34x). Sin embargo, en el Año 2, al comenzar la amortización francesa a 20 años (27.648 €/año de servicio de deuda), el flujo libre solo genera 31.890 €, situando el **DSCR en 1,15x frente al covenant contractual mínimo de 1,25x**.
4. **Restricción Vinculante de Deuda**: Dimensionando la deuda contra un DSCR de 1,25x sobre flujos estables, la capacidad máxima de endeudamiento bancable se reduce a **339.145 €** (32,3% LTV), exigiendo un recorte obligatorio de 28.390 € en la financiación senior.

---

## 2. Comparativa de los tres escenarios

El modelo evalúa tres realidades operativas: el plan original del promotor (reconstruido sobre inductores explícitos), un caso de mercado anclado en datos oficiales de turismo rural del INE y el caso de gestión realista.

| Escenario | Ocupación Año 1 | Ocupación Madura | Ingresos Año 1 | EBITDA Año 1 | DSCR Mínimo | TIR Proyecto (Exit 8,5%) | TIR Equity (Exit 8,5%) | Veredicto Crediticio |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Promotor (Reconstruido)** | 19,20% | 28,92% | 86.275 € | 11.297 € | 0,33x | +6,84% | +12,12% | **Ilíquido** (Caja negativa Años 1–2) |
| **Mercado INE Segovia** | 21,24% | 32,00% | 95.555 € | -18.566 € | -1,46x | -15,18% | -50,22% | **Default** (Deuda inasumible) |
| **Caso Gestión Realista** | 28,23% | 31,36% | 154.548 € | 24.280 € | **1,15x** | **-9,49%** | **-23,16%** | **Denegado** (Incumple covenant 1,25x) |

### Puntos clave de los escenarios
- **Caso Promotor**: Solo arroja rentabilidad positiva en la salida porque ignora los intereses de construcción, el desfase del IVA y las necesidades operativas de capital circulante, entrando en caja negativa en sus dos primeros ejercicios.
- **Mercado INE**: Utiliza la ocupación media real de alojamientos rurales de Segovia (21,24% en 2025, INE EOTR Tabla 2070). Con precios de mercado (85 € ADR y ticket medio de restaurante de 20 €), el EBITDA del Año 1 es negativo (-18.566 €), requiriendo continuas inyecciones del socio para no quebrar.
- **Caso Gestión**: Modela una captura intensiva en fines de semana (31,36% de ocupación estabilizada) y un consumo cautivo en restaurante (ticket de 25 €). Incluso bajo este escenario optimista, el flujo de caja resulta insuficiente para garantizar los márgenes de seguridad de la banca.

---

## 3. Estructura de capital y fuentes y usos

El motor de underwriting despeja el capital propio necesario para que fuentes y usos cuadren exactamente al día de la firma:

| Aplicaciones al Cierre | Importe | Orígenes de Fondos | Importe | % Estructura |
| :--- | ---: | :--- | ---: | :---: |
| **Terreno aportado en especie (25 ha)** | 250.000,00 € | **Deuda Senior Hipotecaria (35% LTV)** | 367.535,00 € | 28,1% |
| **CapEx Obra y Equipamiento** | 800.100,00 € | **Línea Puente de IVA (AEAT)** | 168.021,00 € | 12,9% |
| **Intereses durante construcción (IDC)** | 14.701,40 € | **Equity en Efectivo (Aportación Socio)**| 521.090,22 € | 39,9% |
| **IVA Soportado CapEx (21% s/obra)** | 168.021,00 € | **Equity en Terreno (Aportación Especie)**| 250.000,00 € | 19,1% |
| **Gastos Preoperativos** | 35.000,00 € | | | |
| **Fondo de Maniobra Inicial** | 25.000,00 € | | | |
| **Reserva Servicio Deuda (DSRA 6 meses)**| 13.823,82 € | | | |
| **Total Aplicaciones** | **1.306.646,22 €** | **Total Orígenes** | **1.306.646,22 €** | **100,0%** |

### Apuntes sobre la financiación
- **Mecanismo del Puente de IVA**: Los 168.021 € de IVA soportado en la construcción se financian mediante una póliza de crédito específica al 5,5% de interés, cancelada íntegramente en el Mes 18 tras la liquidación y devolución por parte de la Agencia Tributaria (AEAT).
- **Subvención LEADER**: Los 163.000 € de fondos europeos de desarrollo rural se cobran en el Mes 14, tras la justificación completa de la inversión. Al ser un cobro posterior a la apertura, no puede computarse como liquidez al cierre.
- **Dimensionamiento del DSRA**: La reserva contractual habitual de 6 meses exige 13.824 €. No obstante, la modelización estocástica de cola (Cópula Clayton al 99% CVaR) demuestra que ante una caída severa de demanda se requerirían **62.786 € en reserva líquida** para no suspender pagos de deuda.

---

## 4. Conclusiones principales del underwriting

### 1. El límite vinculante es la cobertura de flujos (DSCR), no la garantía (LTV)
El promotor dimensionó la deuda al 35,0% LTV basándose en el valor de tasación del inmueble terminado. Sin embargo, el flujo de caja del Año 2 (31.890 €) solo permite atender una cuota anual máxima de 25.512 € para cumplir con el covenant de 1,25x. El importe máximo financiable por banca es **339.145 €** (32,3% LTV). Tomar 367.535 € sitúa al prestatario en default técnico inmediato al segundo año.

### 2. La demanda depende de la concentración en fin de semana (occupancy bridge)
La ocupación objetivo de 31,36% (114,5 días ocupados al año) supera en 10,1 puntos porcentuales la media de Segovia (21,24%). El modelo descompone esta brecha de manera auditable:
- **Fines de semana (104 noches)**: 72,0% de ocupación (frente al 48,0% provincial). Explica el 68% de toda la prima de demanda.
- **Puentes y festivos (24 noches)**: 65,0% de ocupación (frente al 45,0% provincial).
- **Días de semana (237 noches)**: 10,1% de ocupación (frente al 7,1% provincial).
Esto demuestra que el proyecto es viable como destino boutique de fin de semana, pero que el mercado corporativo entre semana es prácticamente testimonial.

### 3. La Fase II suspende la prueba de autofinanciación
El promotor planteaba acometer una segunda fase (359.970 € de CapEx para dos suites integradas en el paisaje y biopiscina) financiada con la propia caja generada por la Fase I. Al cierre del Año 2, la tesorería disponible es de solo 183.323 €, arrojando un **déficit de 252.241 €**. Unido a la rotura del covenant, el sistema activa una orden automática de **NO PROCEDER**.

---

## 5. Análisis de reestructuración y opciones de turnaround

El repositorio incluye un módulo de reforma (`case="reform"`) que evalúa ajustes comerciales, optimizaciones de coste y rediseños de producto para estudiar cómo alcanzar la viabilidad institucional.

| Escenario | Estrategia de Turnaround | CapEx Total | Inversión Total | EBITDA Maduración | DSCR Mínimo | Valor Neto Activo (Cap 8,5%) | Brecha Neta vs Inversión | TIR Proyecto | Veredicto |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **R1** | Solo recorte de obra (900k €) | 901.800 € | 986.297 € | 37.042 € | 1,34x | 422.710 € | -563.587 € | -7,18% | Destruye valor |
| **R2** | Reforma comercial (1,05 M€) | 1.050.100 € | 1.138.625 € | 71.321 € | **2,13x** | 813.903 € | -324.723 € | +2,53% | **Salva deuda, Falla valor** |
| **R3** | Reforma + Value Engineering | 901.800 € | 986.297 € | 71.321 € | 2,44x | 813.903 € | -172.394 € | +5,37% | Retorno sub-WACC |
| **R5** | Alcance optimizado (846k €) | 846.300 € | 929.289 € | 71.321 € | 2,57x | 813.903 € | -115.387 € | +6,61% | Retorno sub-WACC |
| **R7** | **Pivote a Cabañas Premium** | **910.000 €** | **1.540.760 €** | **155.713 €** | **1,41x** | **1.589.907 €** | **+49.147 €** | **+9,21%** | **VIABLE (Fase 0 previa)** |

### Conclusiones de la reestructuración
- **La Reforma Comercial (R2)**: Abrir el restaurante a clientes no alojados (6 comensales externos/día a 28 € de ticket), comercializar experiencias agropecuarias (12k €/año) y elevar el ADR un 5% incrementa el EBITDA a 71.321 €. Esto sitúa el DSCR en **2,13x**, resolviendo por completo la solvencia del crédito. Sin embargo, capitalizado a un 8,5% cap rate deduciendo un 3% de costes de venta, el inmueble vale 813.903 €, arrojando una **pérdida de valor neta de 324.723 €** frente a los 1,14 M€ invertidos.
- **El Pivote de Producto (R7)**: Reorientar el desarrollo hacia 6 cabañas bioclimáticas modulares (110k €/cabaña, 200 € ADR, 50% ocupación) proporciona la densidad de ingresos necesaria para alcanzar 155.713 € de EBITDA, superando el WACC del 8,0% con una **TIR de proyecto del 9,21% y un DSCR de 1,41x**.
- **Recomendación Estratégica**: No comprometer 1 M€ en obra civil tradicional sin ejecutar previamente un **test de demanda en Fase 0** (campaña de preventa y pop-up gastronómico con presupuesto de 50k–80k €) para contrastar el apetito real del mercado.

---

## 6. Arquitectura del repositorio y entregables

```
proyecto-dehesa-del-castrillo/
├── main.py                         # Pipeline determinista de 15 pasos
├── README.md / README_ES.md        # Memorandos ejecutivos de underwriting (EN / ES)
├── MODEL_GOVERNANCE_ES.md          # Registro de hipótesis y gobernanza del modelo
├── data/
│   ├── La_Dehesa_del_Castrillo_Financial_Model.xlsx   # Modelo de 22 pestañas y 4.163 fórmulas
│   ├── model_audit_summary.json    # Auditoría computada exportada en JSON
│   └── reform_analysis.json        # Datos de reestructuración y sensibilidades
├── src/
│   ├── config/                     # Parámetros de CapEx, deuda, impuestos e INE
│   ├── core/                       # Motor de 3 estados, amortización, fiscalidad y DSCR
│   ├── simulation/                 # Simuladores de Monte Carlo y cópula de colas
│   └── data/                       # Exportador a Excel con fórmulas dinámicas
└── tests/                          # 17 módulos de test, 121 tests unitarios automáticos
```

### Motor de auditoría computada (16 reglas institucionales)
El código ejecuta una verificación automática en cada corrida (`model_audit.py`):
- **Integridad Contable**: Comprueba que el Activo sea exactamente igual al Pasivo + Patrimonio Neto en todos los años (diferencia de 0,00 €).
- **Cumplimiento Tributario**: Verifica el 10,0% de IVA en hostelería y el 21,0% deducible en CapEx.
- **Cumplimiento Laboral**: Contrasta los costes por hora con el SMI 2026 (RD 126/2026) y las tablas del Convenio Colectivo Provincial de Hostelería de Segovia 2026.
- **Veredicto del Sistema**: `CONDITIONAL - 5 MATERIAL EXCEPTIONS` (reporta con total transparencia las 5 excepciones de riesgo detectadas: DSCR < 1,25x, TIR < WACC y tamaño del equity requerido).

---

## 7. Ejecución y verificación rápida

Requiere **Python 3.11+**:

```bash
# 1. Clonar el repositorio
git clone https://github.com/magnumjpg/la-dehesa-financial-due-diligence.git
cd la-dehesa-financial-due-diligence

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar pipeline completo (genera Excel, JSONs de auditoría y gráficos)
python main.py

# 4. Ejecutar tests unitarios automáticos (121 tests)
pytest -q
```

---

## 8. Autoría y perfil

- **Autor**: Jaime Pérez Gómez ([LinkedIn](https://www.linkedin.com/in/jaime-p%C3%A9rez-656919237/) · [GitHub](https://github.com/magnumjpg))
- **Perfil**: Graduado en Administración y Dirección de Empresas (ADE), Universidad de Alcalá (Madrid). Especializado en modelización financiera, análisis de riesgo de crédito y automatización de procesos con IA y código.
- **Repositorio**: [github.com/magnumjpg/la-dehesa-financial-due-diligence](https://github.com/magnumjpg/la-dehesa-financial-due-diligence)

## Licencia

MIT. Ver [LICENSE](LICENSE).
