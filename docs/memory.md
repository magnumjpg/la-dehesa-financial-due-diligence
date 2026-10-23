# Memoria Continua del Proyecto: La Dehesa del Castrillo

## Lecciones Aprendidas (Mejora Continua)
- 2026-10-23: Inicialización del proyecto de viabilidad financiera y due diligence operativa para La Dehesa del Castrillo.
- Regla de Fuentes Oficiales: Calibrar ocupación con el INE (Encuesta de Ocupación en Alojamientos de Turismo Rural para Segovia) y costes con el Convenio Colectivo Provincial de Hostelería de Segovia.
- Regla de Tono Auténtico: Enfoque en criterio financiero y detección de trampas de papel (IVA, amortizaciones, covenants bancarios DSCR). Cero pretenciosidad o jerga inflada.
- Regla Anti-Estilo IA: Mensajes de commit convencionales humanos, cero em dashes, tablas limpias sin backticks dentro de celdas.
- Lección de Conciliación de Balances: Para garantizar que el Balance cuadre al céntimo ($Activo = Pasivo + Patrimonio$), el crédito fiscal de IVA sobre CapEx debe estructurarse explícitamente en el estado de flujos de caja mediante una línea de financiación puente (póliza de crédito / anticipo bancario de devolución de IVA y LEADER), liquidándose en el Año 2 con el abono de la AEAT.

## Actualidad (Estado y Roadmap Activo)
- [x] Carpeta creada en C:\Users\jaime\Desktop\proyecto-dehesa-del-castrillo con raw_data/, docs/, src/ y assets/.
- [x] Archivos originales importados: La_Dehesa_de_Castrillo_Proyecto.xlsx y Presentacion_La_Dehesa.xlsx.
- [x] Auditoría técnica de raw_data: verificadas fórmulas de CapEx (725k-729k €), convenio Segovia (60.075 € personal), estructura 70/30 de deuda, desfase de IVA y estacionalidad base.
- [x] Fase 1: Extracción, reconciliación empírica y arquitectura de configuración y datos en Python.
- [x] Fase 2: Motor financiero modular en /src (3 estados financieros, FCFF, FCFE, servicio de deuda francés y DSCR/ICR).
- [x] Fase 3: Análisis de escenarios (Conservador, Base, Optimista), matrices de sensibilidad 2D y punto muerto.
- [x] Fase 4: Simulación estocástica Monte Carlo de ocupación, ADR, tipos de interés y cálculo de VaR 95%.
- [x] Fase 5: Generación de figuras institucionales en /assets y redacción del README ejecutivo en inglés.
- [x] Suite de tests automatizados con pytest (16 tests pasando al 100%).
- [x] Pipeline CLI integral en main.py.
