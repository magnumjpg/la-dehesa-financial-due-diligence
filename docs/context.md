# Contexto del Proyecto: La Dehesa del Castrillo

## Título del Proyecto
**La Dehesa del Castrillo: Financial Feasibility, Operational Due Diligence & Scenario Stress-Testing for Rural Hospitality**

## Objetivo General
Desarrollar un modelo financiero cuantitativo e hiperrealista de viabilidad y due diligence operativa para un proyecto hotelero y de restauración rural en Segovia (La Dehesa de Castrillo S.L.). 
A diferencia de los business plans teóricos basados en supuestos optimistas infundados, este proyecto se fundamenta en rigor empírico y corrección de inconsistencias operativas habituales: microdatos de ocupación del INE para turismo rural, estructura de costes laborales según el Convenio Colectivo Provincial de Hostelería de Segovia, desfase de tesorería e IVA, y análisis de cobertura de servicio de la deuda (DSCR) bajo escenarios estresados.

## Hallazgos y Núcleo de Due Diligence (Datos de Origen)
1. Corrección de Inconsistencias Fiscales y de Caja:
   - Error del IVA (21% vs 10%): Aplicar 21% al alojamiento genera una falsa quiebra técnica (-152.250 € en Año 1). Al corregir al 10% legal y modelar el crédito fiscal de la reforma, el Año 1 cierra con solvencia real (+60.750 €).
   - Escudo Fiscal: Amortizaciones (3% obra, 10-13% instalaciones) producen pérdidas contables temporales que evitan el Impuesto de Sociedades en el arranque.
2. Estructura de Inversión (CapEx) y Financiación:
   - Terrenos: 25 Hectáreas en Segovia (250.000 €).
   - Reforma integral (550 m²): 440.000 €.
   - Biopiscina y paisajismo: 35.000 €.
   - Total Inversión Base: 725.000 €. Estructura 70% Deuda Hipotecaria / 30% Fondos Propios.
3. Costes Operativos Calibrados con Convenio Real (Segovia):
   - Categorías laborales reales (Cocinera I, Cocinera II, Limpieza Grupo III) con 35% SS patronal obligatoria.
4. Calibración de Demanda y Ocupación (INE Segovia):
   - Estacionalidad mensual real (~19% valle invierno, ~42% pico verano/fines de semana).

## Arquitectura del Proyecto
1. raw_data/: Excels originales (La_Dehesa_de_Castrillo_Proyecto.xlsx y Presentacion_La_Dehesa.xlsx).
2. src/: Motor financiero en Python, escenarios, Monte Carlo y visualización.
3. docs/: context.md y memory.md.
4. README.md: Memorando de inversión ejecutivo en inglés.
