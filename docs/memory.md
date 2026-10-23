# Memoria Continua del Proyecto: La Dehesa del Castrillo

## Lecciones Aprendidas (Mejora Continua)
- 2026-10-23: Inicialización del proyecto de viabilidad financiera y due diligence operativa para La Dehesa del Castrillo.
- Regla de Fuentes Oficiales: Calibrar ocupación con el INE (Encuesta de Ocupación en Alojamientos de Turismo Rural para Segovia) y costes con el Convenio Colectivo Provincial de Hostelería de Segovia.
- Regla de Tono Auténtico: Enfoque en criterio financiero y detección de trampas de papel (IVA, amortizaciones, covenants bancarios DSCR). Cero pretenciosidad o jerga inflada.
- Regla Anti-Estilo IA: Mensajes de commit convencionales humanos, cero em dashes, tablas limpias sin backticks dentro de celdas.
- Lección de Conciliación de Balances: Para garantizar que el Balance cuadre al céntimo ($Activo = Pasivo + Patrimonio$), el crédito fiscal de IVA sobre CapEx debe estructurarse explícitamente en el estado de flujos de caja mediante una línea de financiación puente (póliza de crédito / anticipo bancario de devolución de IVA y LEADER), liquidándose en el Año 2 con el abono de la AEAT.
- Lección de Doble Calibración Operativa: Los Excels originales presentaban dos niveles: (1) proyección preliminar LEADER simplificada (96k € ventas Año 1 con 66,3 días ocupados equivalentes / 18,2% ocupación) y (2) microdatos reales del INE Segovia (31,4% ocupación / 154k € Año 1). Ambos modos deben estar soportados y documentados para que cualquier revisor bancario o recruiter comprenda la evolución del modelo sin encontrar discrepancias.
- Alineación de Estilo con Portafolio: README bilingüe (EN/ES), cuadro de mando en caja ASCII/Unicode, fórmulas LaTeX explícitas y generación automatizada del modelo Excel multicapa (.xlsx) en /data.

## Actualidad (Estado y Roadmap Activo)
- [x] Carpeta creada en C:\Users\jaime\Desktop\proyecto-dehesa-del-castrillo con raw_data/, docs/, src/ y assets/.
- [x] Archivos originales importados: La_Dehesa_de_Castrillo_Proyecto.xlsx y Presentacion_La_Dehesa.xlsx.
- [x] Auditoría técnica de raw_data: verificadas fórmulas de CapEx (725k-729k €), convenio Segovia (60.075 € personal), estructura 70/30 de deuda, desfase de IVA y estacionalidad base.
- [x] Fase 1: Extracción, reconciliación empírica y arquitectura de configuración y datos en Python.
- [x] Fase 2: Motor financiero modular en /src (3 estados financieros, FCFF, FCFE, servicio de deuda francés y DSCR/ICR).
- [x] Fase 3: Análisis de escenarios (Conservador, Base, Optimista), matrices de sensibilidad 2D y punto muerto.
- [x] Fase 4: Simulación estocástica Monte Carlo de ocupación, ADR, tipos de interés y cálculo de VaR 95%.
- [x] Fase 5: Generación de figuras institucionales en /assets y redacción del README ejecutivo en inglés y español.
- [x] Exportador de modelo financiero en Excel (.xlsx con 5 pestañas formateadas en /data).
- [x] Suite de tests automatizados con pytest (16 tests pasando al 100%).
- [x] Pipeline CLI integral en main.py y repositorio Git limpio con commits convencionales.
