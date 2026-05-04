# Explicación del proyecto: Detección de lesiones cutáneas con YOLO

## ¿Qué estamos haciendo?

Entrenamos un modelo de deep learning para que, dada una imagen dermatoscópica (foto clínica de la piel tomada con un dermatoscopio), sea capaz de:

1. **Localizar** la lesión dentro de la imagen (dibujar un bounding box)
2. **Clasificar** de qué tipo de lesión se trata entre 7 categorías

El resultado es una aplicación que cualquier usuario puede usar para subir una foto y obtener un diagnóstico automático con nivel de confianza.

---

## El dataset: HAM10000

**HAM10000** (Human Against Machine with 10000 training images) es un dataset público del Harvard Dataverse con 10.015 imágenes dermatoscópicas etiquetadas por dermatólogos expertos.

Contiene 7 clases de lesiones:

| Código | Nombre completo | Tipo |
|--------|----------------|------|
| `nv` | Melanocytic Nevus | Benigno (lunar común) |
| `mel` | Melanoma | **Maligno** |
| `bkl` | Benign Keratosis | Benigno |
| `bcc` | Basal Cell Carcinoma | **Maligno** |
| `akiec` | Actinic Keratosis | Pre-maligno |
| `vasc` | Vascular Lesion | Benigno |
| `df` | Dermatofibroma | Benigno |

El dataset tiene un **fuerte desbalance de clases**: `nv` tiene 6.705 imágenes mientras que `df` solo tiene 115. Esto afecta al rendimiento del modelo en las clases minoritarias.

---

## El modelo: YOLOv8

**YOLO** (You Only Look Once) es una familia de modelos de detección de objetos en tiempo real. Usamos la versión 8, variante **nano** (`yolov8n`), que es la más ligera de la familia.

### ¿Por qué YOLO para dermatología?

El dataset HAM10000 contiene imágenes donde la lesión ocupa gran parte del encuadre. YOLO permite hacer detección + clasificación en un solo paso: localiza la lesión con un rectángulo (bounding box) y simultáneamente predice su clase.

### Arquitectura simplificada

```
Imagen de entrada (224×224 px)
        ↓
   Backbone CSPDarknet
   (extrae características visuales: bordes, texturas, colores)
        ↓
   Neck FPN (fusiona características a distintas escalas)
        ↓
   Detection Head
   (predice: dónde está la lesión + qué clase es + qué confianza tiene)
        ↓
   Bounding box + clase + confianza
```

---

## El proceso paso a paso

### 1. Preparación del dataset (`scripts/prepare_dataset.py`)

YOLO necesita los datos en un formato específico. Por cada imagen debe existir un fichero `.txt` con una línea por cada objeto detectado:

```
<clase> <x_centro> <y_centro> <ancho> <alto>
```

Todos los valores están normalizados entre 0 y 1 (relativos al tamaño de la imagen).

Para obtener el bounding box usamos las **máscaras de segmentación** incluidas en el dataset: son imágenes binarias (blanco = lesión, negro = fondo) de las que extraemos el rectángulo mínimo que contiene la lesión.

```
Máscara binaria  →  cv2.findNonZero()  →  cv2.boundingRect()  →  coordenadas YOLO
```

El dataset se divide en **80% entrenamiento / 20% validación**, estratificado por clase para mantener la proporción de cada una en ambas particiones.

### 2. Entrenamiento (`scripts/train.py`)

```
yolov8n.pt (pesos preentrenados en COCO)
        ↓
  Fine-tuning sobre HAM10000
  50 épocas, batch=16, imgsz=224, CPU
        ↓
  results/train/weights/best.pt   ← mejor modelo (mayor mAP en validación)
  results/train/weights/last.pt   ← último checkpoint (permite reanudar)
```

Se usa **transfer learning**: el modelo ya sabe detectar objetos genéricos (entrenado en COCO con 80 clases) y lo especializamos para lesiones cutáneas. Esto permite entrenar con menos datos y menos tiempo.

### 3. Evaluación (`scripts/evaluate.py`)

Una vez entrenado, evaluamos el modelo sobre el conjunto de validación y calculamos:

- **Precision**: de todas las veces que dijo "es melanoma", ¿cuántas eran realmente melanoma?
- **Recall**: de todos los melanomas reales, ¿cuántos detectó correctamente?
- **F1-score**: media armónica de precision y recall (equilibrio entre ambas)
- **mAP@0.5**: mean Average Precision — métrica estándar en detección de objetos. Mide la precisión promedio cuando el bounding box predicho solapa ≥50% con el real.
- **Matriz de confusión**: muestra qué clases se confunden entre sí.

### Resultados obtenidos

| Métrica | Valor |
|---------|-------|
| Accuracy global | **84%** |
| mAP@0.5 | **0.731** |
| mAP@0.5:0.95 | **0.575** |

| Clase | Precision | Recall | F1 | Interpretación |
|-------|-----------|--------|----|----------------|
| `nv` | 0.90 | 0.95 | **0.93** | Excelente — clase dominante |
| `vasc` | 0.81 | 0.93 | **0.87** | Muy bueno — visualmente distinta |
| `bcc` | 0.84 | 0.62 | 0.72 | Bueno |
| `bkl` | 0.66 | 0.75 | 0.70 | Bueno |
| `df` | 0.75 | 0.52 | 0.62 | Aceptable — pocos ejemplos |
| `mel` | 0.67 | 0.50 | **0.57** | Preocupante clínicamente |
| `akiec` | 0.61 | 0.38 | **0.47** | El peor — solo 130 muestras |

**Punto crítico**: el modelo detecta mal el melanoma (`mel`, F1=0.57). Esto se debe a que morfológicamente es muy similar a `nv` (los nevos) y el dataset tiene un fuerte desbalance. En un contexto clínico real esto requeriría mejoras (oversampling, data augmentation específico, modelo más grande).

---

## La aplicación (`app/main.py`)

Se lanza con `python app/main.py` y abre automáticamente en el navegador en `http://localhost:7860`.

Está construida con **Gradio**, una librería Python para crear interfaces web de ML de forma muy simple. Corre completamente en local, no envía nada a internet.

### Lo que puedes ver en cada pestaña

---

### Pestaña 1 — Detección

Aquí es donde el modelo hace su trabajo en tiempo real.

**Cómo usarla:**
1. Haz clic en el área de imagen o arrastra una foto dermatoscópica
2. Pulsa **Analizar**
3. En la imagen de la derecha aparece el bounding box sobre la lesión con su etiqueta y confianza
4. Debajo del resultado aparece el nombre completo de la lesión y las coordenadas del box

**Qué significa la confianza:** es la probabilidad que el modelo asigna a su predicción. Un 85% significa que el modelo está bastante seguro. Por debajo del 50% la predicción es poco fiable.

---

### Pestaña 2 — Métricas por clase

Muestra tres gráficas de barras horizontales:
- **Precision** por clase
- **Recall** por clase
- **F1-score** por clase

Permite ver de un vistazo qué clases el modelo domina y cuáles le cuestan. Se aprecia claramente el efecto del desbalance: `nv` y `vasc` tienen barras muy largas, mientras `akiec` y `mel` tienen las más cortas.

Encima de las gráficas aparece el resumen global (mAP y el reporte de clasificación completo).

---

### Pestaña 3 — Curvas de entrenamiento

Cuatro gráficas que muestran cómo evolucionó el aprendizaje a lo largo de las 50 épocas:

- **Classification Loss** (train vs val): mide el error al predecir la clase. Debe bajar progresivamente.
- **Box Loss** (train vs val): mide el error al predecir la posición del bounding box. También debe bajar.
- **mAP@0.5**: debe subir. Refleja la mejora de detección.
- **mAP@0.5:0.95**: igual pero con un criterio de solapamiento más estricto.

La línea azul es el conjunto de entrenamiento y la roja discontinua es validación. Si la curva de validación sube pero luego se estabiliza mientras la de entrenamiento sigue bajando, hay **overfitting** (el modelo memoriza en lugar de generalizar).

---

### Pestaña 4 — Matriz de confusión

Una tabla donde cada fila es la clase real y cada columna es la clase que predijo el modelo. La diagonal principal (de arriba izquierda a abajo derecha) son los aciertos.

**Cómo leerla:**
- Un cuadrado muy oscuro en la diagonal = el modelo acierta bien esa clase
- Un cuadrado oscuro fuera de la diagonal = el modelo confunde una clase con otra

Por ejemplo, se puede ver que `mel` se confunde frecuentemente con `nv`, lo cual tiene sentido porque morfológicamente son similares.

---

## Resumen visual del flujo completo

```
HAM10000 dataset
(imágenes + CSV + máscaras)
        ↓
prepare_dataset.py
(convierte a formato YOLO)
        ↓
train.py
(entrena YOLOv8n, 50 épocas)
        ↓
evaluate.py
(métricas, confusion matrix)
        ↓
app/main.py
(interfaz Gradio en navegador)
```
