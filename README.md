# Epidermix — Detección de Lesiones Cutáneas con YOLOv8

> Proyecto de la asignatura **Bioinformática y Medicina**  
> Grado en Inteligencia Artificial — Universidade da Coruña  
> Curso 2025-2026

Epidermix es una aplicación web de apoyo al diagnóstico dermatológico. A partir de una imagen de una lesión cutánea, el sistema detecta y localiza automáticamente la lesión, la clasifica en una de las 7 categorías clínicas del dataset HAM10000 y proporciona información médica sobre el diagnóstico. En caso de lesión de riesgo alto, la app ofrece acceso directo a la solicitud de cita médica en el SERGAS.

El sistema está formado por tres componentes: un modelo YOLOv8-small entrenado sobre 10.015 imágenes dermatoscópicas reales (mAP@0.5 = 0.808), una API REST construida con FastAPI que sirve las predicciones, y una aplicación web desarrollada en Flutter accesible desde cualquier navegador sin instalación.

**Stack:** Flutter Web · FastAPI · YOLOv8 · HAM10000

---



## Clases detectadas

| ID | Código | Nombre | Riesgo |
|----|--------|--------|--------|
| 0 | akiec | Queratosis Actínica | Alto |
| 1 | bcc | Carcinoma Basocelular | Alto |
| 2 | bkl | Queratosis Benigna | Bajo |
| 3 | df | Dermatofibroma | Bajo |
| 4 | mel | Melanoma | Alto |
| 5 | nv | Nevo Melanocítico | Bajo |
| 6 | vasc | Lesión Vascular | Bajo |

---

> **Aviso legal:** Este sistema es orientativo y no reemplaza el diagnóstico médico profesional.
