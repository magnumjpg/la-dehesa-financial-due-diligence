# Red team: diecisiete ataques al modelo de la Dehesa del Castrillo

**Propósito.** Este memo es la contraparte adversarial del caso de inversión. Asume que el lector cobra por encontrar el punto más débil del modelo, no por aprobarlo. Cada ataque va seguido de lo que el libro dice realmente, lo que concedo y lo que sigue sin resolverse.

**Conclusión.** El red team no rescata el proyecto. Seis ataques refuerzan el decline, tres exponen debilidades reales de la reforma (cubiertos externos, personal y cap rate de salida) y uno es un problema de presentación. Las tres debilidades reales son exactamente la razón por la que la recomendación es un test de demanda de Fase 0 de bajo coste y no un presupuesto de construcción.

**Nota de consistencia.** Las cifras de abajo son las que produce el pipeline actual (`python main.py`) y las que fija la batería de tests. R6 está anclado a la ocupación INE del 21,24% y su valor de empresa está limitado a cero; las pérdidas operativas se mantienen en el VAN.

---

## Ataque 1: "El 31,36% está un 48% por encima del INE. Te has inventado la demanda."

**Por qué duele.** La media oficial del INE para Segovia en 2025 es 21,24% (77,5 días ocupados por habitación disponible). El caso de gestión asume 31,36%, o 114,5 días ocupados. En apariencia es un +48% en todas las noches del año.

**Qué dice el modelo.** La media anual es una mezcla de tres segmentos, no un uplift plano:

| Segmento | Noches | Gestión | INE | Gap (pp) |
|---|---:|---:|---:|---:|
| Viernes-sábado | 104 | 72,0% | 48,0% | +6,84 |
| Puentes festivos | 24 | 65,0% | 45,0% | +1,32 |
| Entre semana | 237 | 10,1% | 7,1% | +1,97 |
| **Anual** | **365** | **31,36%** | **21,24%** | **+10,12** |

El 68% del gap es captura de fin de semana. El supuesto entre semana está solo 3,0 pp por encima del mercado. El Año 1 es deliberadamente más débil, al 0,90x de la curva madura (28,23%).

**Respuesta.** La forma es plausible para un boutique de destino con restaurante: fines de semana fuertes, martes débiles. El puente cuadra exactamente con el 31,36% del modelo y no puede cambiar la P&L. La auditoría, no obstante, falla la Regla 10 a 1,48x la media del INE, así que el caso está etiquetado como upside, no como base.

**Riesgo residual.** Los anclajes del 72% y el 65% son juicio, no medición. No hay curva de reservas, competitive set ni datos de ritmo de OTA. Un anclaje de fin de semana del 60% bajaría la ocupación anual a unos 27%, por debajo del break-even del covenant.

---

## Ataque 2: "Tu caso de mercado llega al 32% igualmente, así que el downside no es un downside."

**Por qué duele.** El caso de mercado INE empieza en 21,24% pero mantiene la rampa de volumen del promotor (25%/20%) y el crecimiento nominal del 5% desde el Año 4, así que llega al 32,0% en el Año 3. Si el "downside" alcanza la misma ocupación que el "upside", las etiquetas engañan.

**Qué dice el modelo.** Con el 21,24% oficial en el Año 1 el caso de mercado produce ingresos de 95.555 €, EBITDA de -18.566 € y un DSCR de -1,46x. Nunca supera 1,0x en cinco años. Lo que lo lleva al 32% es la rampa, no el anclaje de ocupación.

**Respuesta.** La rampa es un supuesto heredado del Excel original y está declarado. El caso de mercado es un downside de economía unitaria y servicio de deuda, no una afirmación de que la demanda se quede en 21,24% durante cinco años. Una versión más estricta mantendría la ocupación en 21,24% todo el horizonte; eso es lo que hace R6 en la capa de reforma.

**Riesgo residual.** Mezclar un punto de partida INE con una rampa de promotor es una debilidad de presentación. Un lector puede pedir razonablemente un caso as-is plano al 21,24%; la capa de reforma ofrece el test equivalente.

---

## Ataque 3: "Cobras 250k por un terreno que la familia ya tiene."

**Por qué duele.** Si el terreno se aporta en especie, el proyecto no necesita escribir un cheque por él. Cargarlo hace que el retorno parezca peor.

**Qué dice el modelo.** El terreno se lleva a su valor de oportunidad (250.000 €) tanto en los casos as-is como en la reforma. El equity total en el cierre incluye el terreno en especie. Las fuentes y usos solo cuadran con un equity plug en caja de 521.090 € más la aportación del terreno.

**Respuesta.** El valor de oportunidad es el cargo correcto. Tratar el terreno como gratis convertiría una subvención familiar en retorno del proyecto y favorecería todas las métricas. El modelo muestra el terreno por separado para que el lector pueda quitarlo y ver el negocio operativo solo.

**Riesgo residual.** Los 250k € son un supuesto de tasación, no una oferta vinculante. Si el terreno vale más, el proyecto es peor, no mejor.

---

## Ataque 4: "Un cap rate del 8,5% es demasiado bajo para la Segovia rural."

**Por qué duele.** Los activos hoteleros rurales en provincias de baja densidad cotizan a yields más amplios. Un cap rate del 10-11% es defendible, y el caso base usa 8,5%.

**Qué dice el modelo.** R6 usa un cap rate de salida del 10%. Cada +100 pb quita unos 76k € de valor bruto. A un cap rate del 10%, el valor de empresa de R2 cae a 713.214 € y el gap neto frente a la inversión total se amplía a -446.808 €.

**Respuesta.** El 8,5% es un supuesto de caso base, y la sensibilidad es explícita. La conclusión no depende de él: el caso falla al 8,5% y falla más al 10%.

**Riesgo residual.** El múltiplo de salida es 11,8x EBITDA al 8,5%, alto para un activo rural. El modelo sería más fuerte con un cap rate derivado de transacciones comparables; no hay ninguna en el repositorio.

---

## Ataque 5: "Seis cubiertos externos de F&B al día es inventado."

**Por qué duele.** Es la palanca más grande de la reforma. Añade 61.320 € de ingresos maduros y 13.698 € de EBITDA. No hay evidencia en el repositorio de que la finca pueda atraer seis cubiertos externos al día, especialmente entre semana.

**Qué dice el modelo.** Con seis cubiertos, R2 alcanza 71.321 € de EBITDA y un DSCR de 2,13x. Con tres cubiertos (R6), el EBITDA se vuelve negativo (-33.887 €) y el DSCR es -3,82x.

**Respuesta.** Concedido. El supuesto no está probado. Es exactamente por eso que la recomendación no es "constrúyelo" sino "haz primero un test de Fase 0 con un pop-up o un restaurante arrendado". El modelo es una herramienta para poner precio al test, no un sustituto del test.

**Riesgo residual.** Es el punto más débil de la reforma. Si los cubiertos se quedan por debajo de cuatro, la reforma no funciona con ningún CapEx plausible.

---

## Ataque 6: "Un FTE no puede con seis cubiertos y los desayunos."

**Por qué duele.** Seis cubiertos externos más hasta 21 huéspedes internos es un servicio completo. Un FTE cargado a 28k € es un escalón de personal fino.

**Qué dice el modelo.** R2 añade un FTE; R6 añade 1,5. Mover R2 a 1,25-1,5 FTE reduciría el EBITDA en unos 7k-14k € y ampliaría el gap neto en la misma cantidad.

**Respuesta.** Concedido como debilidad del caso base. La base actual es el mínimo escalón de personal, no el cómodo. Una base de 1,5 FTE empeoraría el gap de R2 pero no cambiaría la dirección de la conclusión.

**Riesgo residual.** La programación, la rotación y la inflación salarial no están modeladas. La nómina es a tiempo parcial y cumple en precio/hora, pero el riesgo de cobertura sigue.

---

## Ataque 7: "Tu Monte Carlo es un gaussiano naive."

**Por qué duele.** La ocupación y el ADR hotelero tienen colas gruesas y están correlacionados. Una simulación gaussiana subestima el downside conjunto.

**Qué dice el modelo.** El Monte Carlo gaussiano se mantiene como benchmark. El motor de cúpulas compara dependencia gaussiana, Student-t y Clayton. El CVaR 99% de Clayton implica una DSRA de 62.786 € frente a la reserva contractual de 13.824 €.

**Respuesta.** Correcto. La cúpula es la herramienta real de cola, y la recomendación de DSRA es de seis meses contractuales frente a la cifra mayor basada en la cola. Usar la reserva mayor ampliaría la necesidad de equity.

**Riesgo residual.** Las marginales de la cúpula siguen siendo supuestos calibrados. Es un mejor modelo de cola, no uno validado.

---

## Ataque 8: "El VAN unlevered subestima el caso de equity; el apalancamiento puede rescatarlo."

**Por qué duele.** El VAN de proyecto ignora el valor de la opción de apalancamiento y el upside del equity.

**Qué dice el modelo.** El covenant DSCR limita la facilidad a 339.145 € frente a los 367.535 € solicitados. La TIR de equity de R2 es 1,96%; la de R4 es 10,16%, pero solo en el rincón no probado de ocho cubiertos. El proyecto no gana su coste de capital del 8% a nivel operativo.

**Respuesta.** El apalancamiento no crea valor cuando el yield del activo está por debajo del coste de la deuda. Puede amplificar un spread positivo, no fabricarlo. Los retornos de equity confirman el punto: la TIR de equity de R2 está por debajo de la TIR de proyecto.

**Riesgo residual.** Otro stack de capital (mezzanine, equity de subvención, pago diferido del terreno) podría cambiar el resultado de equity, pero no cambiaría el gap de valor a nivel de activo.

---

## Ataque 9: "Duplicas la subvención e ignoras el timing del IVA."

**Por qué duele.** La subvención LEADER y el reembolso de IVA son dos entradas de dinero público. Si financian los mismos costes dos veces, el stack de financiación está sobrestimado.

**Qué dice el modelo.** La subvención es una fuente de capital (162.766 € en R2), no un ingreso. El puente de IVA es una facilidad separada de 175.000 € dispuesta sobre el IVA del CapEx, repagada con el reembolso de la AEAT en el Mes 18, y devenga intereses. El gate de Fase II prueba el doble gasto y devuelve `DO NOT PROCEED`.

**Respuesta.** No hay doble cómputo en el modelo de financiación. La subvención reduce equity, el puente de IVA es liquidez temporal, y el phase gate es el control que impide gastar los dos dos veces.

**Riesgo residual.** No hay carta de concesión en el repositorio. La subvención se trata como comprometida en el Mes 14/Año 2; el stress sin subvención cuesta 119.838 € de VAN.

---

## Ataque 10: "Una salida en el Año 5 a 11,8x EBITDA domina el resultado."

**Por qué duele.** El valor terminal es grande respecto a los flujos operativos. Un pequeño cambio en el cap rate mueve la TIR.

**Qué dice el modelo.** Sin salida, la TIR de proyecto de gestión es -35,43%. Con salida al 8,5% es -9,49%. La salida hace la caída más pequeña, no convierte el caso en exitoso. El test neto de costes se muestra por separado (3% del valor; 4% en R6).

**Respuesta.** La salida es un test, no un rescate. Se muestran ambas, con y sin salida. El cap rate se estresa al 10% en R6, y los ingresos netos se muestran junto al valor bruto.

**Riesgo residual.** El valor terminal sigue asumiendo un mercado de venta funcionando en el Año 5. Una venta forzada o un cap rate de distress produciría un resultado peor que el caso base.

---

## R7: cinco ataques más, porque el caso de cabañas sí pasa

R7 es la única configuración del libro que supera a la vez el WACC y el test neto de inversión total. Eso lo convierte en el caso que un comité de crédito atacaría con más dureza, no en el que dejaría pasar sin preguntas.

## Ataque 11: "110 k€ all-in por cabaña es precio de catálogo, no de una unidad de hospitalidad."

**Por qué duele.** Si el coste real es 130 k€, el gap neto se vuelve -87.672 € y el caso falla. La base solo está un 3,2% por encima del agua.

**Qué dice el modelo.** La escalera de coste es explícita: 110 k€ pasa (+49.147 €), 120 k€ falla (-19.263 €), 130 k€ falla (-87.672 €), 150 k€ falla (-224.490 €) y 180 k€ falla (-429.718 €). Los 110 k€ no son precio de cáscara: incluyen la unidad equipada, la terraza, servicios y la parte proporcional de infraestructura común. La nota separa la cáscara de 17-37 k€ del paquete instalado estándar de 85-110 k€ y del premium de 130-150 k€.

**Respuesta.** La base está deliberadamente en el techo del corredor estándar, no en el centro del premium. La recomendación no dice "construir a 110 k€"; dice "hacer el test de Fase 0 y luego conseguir una oferta vinculante a 110 k€ o menos".

**Riesgo residual.** Una oferta de QS a 125-135 k€ es perfectamente plausible en 2026. Si llega, lo correcto es recortar una cabaña o el alcance del restaurante, no subir el ADR.

## Ataque 12: "200 € de ADR para una cabaña en Segovia es optimista."

**Por qué duele.** La muestra local de OTAs promedia 236 €/noche pero va de 85 a 520 €; la mediana está muy por debajo de la media, y los 200 € son una tarifa realizada anual, no un precio de fin de semana punta.

**Qué dice el modelo.** Con 190 € de ADR y 50% de ocupación el gap neto es -39.932 €. Con 200 € es +49.147 €. El caso vive en una banda de 10-20 € alrededor de la tarifa realizada. El stretch necesita 230 € y 55%, y la nota dice explícitamente que 250 €+ no está soportado.

**Respuesta.** Los 200 € están triangulados con tres fuentes (muestra OTA, tarifas de casas rurales por persona, bandas de operadores de glamping), no con un anuncio suelto. El downside corre a 190 €.

**Riesgo residual.** Si la tarifa realizada se queda en 185-190 €, R7 falla incluso a 110 k€. Para eso está el test de Fase 0.

## Ataque 13: "45 k€ de experiencias agronómicas es un relato, no una línea de ingreso."

**Por qué duele.** Los 45 k€ son el 7,9% del ingreso total y llevan un margen del 70%, así que contribuyen de forma desproporcionada al EBITDA. Si en realidad son 25 k€, el gap neto cae unos 14 k€ y la base deja de pasar.

**Qué dice el modelo.** La nota construye los 45 k€ de dos formas: 30 retiros × 12 personas × 125 €, o 300 experiencias × 150 €, que es un attach del 27% sobre 1.095 noches de cabaña. El downside usa 25 k€.

**Respuesta.** Las experiencias se modelan con anfitrión, calendario y marketing explícitos dentro de los 4,5 FTE y del OPEX fijo, no como ingreso pasivo. El gate de Fase 0 incluye el attach realizado.

**Riesgo residual.** Un attach del 27% es exigente para una primera temporada. El caso debería re-ejecutarse con un attach del 15-20% antes de comprometer construcción.

## Ataque 14: "Seis cabañas son cuatro demasiadas para una primera fase."

**Por qué duele.** Construir las seis antes de probar la demanda convierte una opción de 50 k€ en un compromiso de 1,54 M€. El downside (cinco cabañas) sigue perdiendo 989 k€.

**Qué dice el modelo.** Cinco cabañas a 110 k€ con 45 k€ de experiencias pasan el test de activo (+49.987 €) pero fallan el de inversión total (-29.183 €). La sexta cabaña es lo que hace pasar el caso, porque añade unos 21 k€ de EBITDA por 110 k€ de CapEx, un yield on cost del 19%.

**Respuesta.** La recomendación es explícitamente en dos fases: la Fase 0 prueba la demanda con dos cabañas más la casa, y solo después se construye la sexta. El modelo pone precio a la configuración completa; la recomendación no la autoriza de golpe.

**Riesgo residual.** Una construcción por fases tiene su propio sobrecoste y pierde las economías de escala de la infraestructura común.

## Ataque 15: "Cobras 250 k€ por un terreno que la familia ya tiene, así que el resultado no es el retorno de la familia."

**Por qué duele.** El retorno que le importa a la familia es la caja que realmente pone. Si el terreno se aporta en especie y nunca se paga, el cheque de equity es menor y la TIR de la familia es mayor que la TIR de proyecto.

**Qué dice el modelo.** Los 250 k€ están en todas las métricas de R7, incluida la base de 110 k€. Quitarlos añadiría unos 250 k€ al gap y haría el caso mejor, no peor: R7 pasa *con* el terreno cargado. El test de proyecto es deliberadamente el del activo completo, porque el banco presta contra el activo completo y el terreno tiene valor de oportunidad (se podría vender o arrendar).

**Respuesta.** El terreno se queda dentro, y la vista de caja de equity se muestra por separado. El caso no pasa por fingir que la finca es gratis; la familia puede ver un retorno mejor solo-para-ella si quiere, pero esa no es la misma decisión.

**Riesgo residual.** Los 250 k€ son un valor de oportunidad interno, no una tasación. Una valoración formal podría moverlo en cualquier dirección, y con ella el tamaño del gap.

## Ataque 16: "Todo tu gap de +49 k€ son 30 puntos básicos de compresión de cap rate."

**Por qué duele.** El yield on cost de desarrollo es 10,11% y el cap de salida es 9,50%. El cap de equilibrio es 9,80%, así que el caso pasa por 30 pb. Sin compresión, el gap neto es -46.223 €, que es exactamente la factura de costes de salida del 3%. El "beneficio" es el diferencial entre lo que cuesta construir y el cap al que se vende.

**Qué dice el modelo.** El contraste de valoración muestra el yield on cost, el cap de equilibrio y el caso sin compresión junto al gap titular. La tabla de múltiplos es explícita: a 9,0x el gap neto es -181.390 €, a 10,5x es +45.172 € y a 12,0x es +271.733 €. La base está en 10,53x, así que necesita que la salida ocurra a un yield más ajustado que el que implica el coste de construcción.

**Respuesta.** El gap se etiqueta como diferencial de desarrollo, no como creación de valor operativo. El cap de salida del 9,5% ya es el caso central, no uno agresivo, y el gate de Fase 0 incluye una opinión de tasador local antes de comprometer capital de construcción. Si el tasador confirma 9,8% o mejor, el caso sobrevive; si no, no.

**Riesgo residual.** Los cap rates de la Segovia rural para una operación de seis llaves podrían estar en 10,0-10,5%. Al 10,5% R7 falla incluso con la cabaña a 110 k€, y ningún ADR arregla un problema de cap rate.

## Ataque 17: "Modelas cinco años de costes planos. ¿Dónde está la inflación?"

**Por qué duele.** La nómina, la energía y el mantenimiento no se quedan planos cinco años. Si los costes reales crecen un 2% anual mientras el ADR se queda plano, el gap neto cae de +49.147 € a -142.819 €. Al 2,5% es -192.609 € y al 3% es -243.134 €. La base no tiene margen para un diferencial real coste-precio.

**Qué dice el modelo.** Las capas de reforma y R7 están en euros constantes de 2026 en ambos lados: ADR, nómina y OPEX planos. Es internamente coherente y está declarado. El stress de inflación rompe la simetría a propósito para aislar la compresión de margen, porque un modelo nominal completo necesitaría ingresos indexados y un WACC nominal; indexar solo los ingresos inflaría el valor terminal frente a un CapEx gastado en t=0.

**Respuesta.** El stress se reporta como escenario, no como previsión, y la conclusión base no depende de que los costes se queden planos para siempre. El gate de Fase 0 debería incluir una cotización de nómina y energía, y la familia debería tratar el margen del 3,2% como contingente a mantener la base real de costes.

**Riesgo residual.** Si la nómina y la energía superan al ADR en un 2% anual, R7 falla con cualquier coste de cabaña dentro del corredor. Es un problema estructural de margen, no de construcción.

---

## Qué cambiaría el veredicto

El decline es robusto a los ataques anteriores, pero no es infalsificable. Tres piezas de evidencia obligarían a re-ejecutar:

1. **Un test de demanda de Fase 0 firmado** que muestre al menos cuatro cubiertos externos al día, sostenidos entre semana, con un menú y un precio que superen el ticket asumido de 28 €.
2. **Un presupuesto de obra vinculante de 900k € o menos** para el alcance lean, con informe de QS y una contingencia que sobreviva a un sobrecoste del 20%.
3. **Una carta de concesión LEADER** con fecha de desembolso, más un term sheet de deuda dimensionado al tope DSCR en lugar del 35% LTV.

Aun con las tres, R2 necesitaría un cap rate por debajo de aproximadamente 7,2% para superar el test de inversión total con 71.321 € de EBITDA. Eso no es un cap rate de la Segovia rural. La conclusión honesta es que el proyecto es una **opción de Fase 0**, no un proyecto de construcción.

Para R7 la lista es distinta y más estrecha: una temporada de Fase 0 firmada con 45% de ocupación, 190 € de ADR realizado, ocho cubiertos externos al día y 25 k€ de experiencias, más una oferta vinculante de cabaña all-in a 110 k€ o menos. Si falla el gate de ocupación, el caso muere independientemente del ADR; si falla el de coste, la respuesta es menos cabañas o un restaurante más pequeño, no un precio más alto. Hay dos condiciones más, ya explícitas: una opinión de tasador con cap de salida igual o inferior al 9,8%, y un diferencial real coste-precio no peor que el 1% anual.

---

## Cuestiones abiertas que no he resuelto

- Los anclajes de ocupación de fin de semana y puentes son juicio, no medición.
- El reparto del INE se infiere de la media anual, no lo publica el INE.
- La demanda de cubiertos externos no tiene competitive set ni build-up por franja.
- El personal está en el mínimo escalón, no en el cómodo.
- El cap rate de salida no está soportado por transacciones comparables.
- El valor de empresa cero de R6 es un suelo contable, no un análisis de liquidación.
- La sensibilidad de tipos es una re-ejecución a tipo fijo, no un modelo de refinanciación.
- Los 45 k€ de experiencias de R7 no tienen programa firmado, solo un build-up.
- El coste all-in de 110 k€ por cabaña de R7 es un benchmark, no una oferta de contratista.
- R7 pasa por 30 pb de diferencial de cap rate y por una base de costes real plana; ambas son supuestos, no evidencia.

Estas cuestiones aparecen en la sección de limitaciones del README. No están escondidas en un apéndice.
