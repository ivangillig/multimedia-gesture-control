# 🎵 Control Multimedia con Reconocimiento de Manos

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.0+-green.svg)](https://opencv.org)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10+-orange.svg)](https://mediapipe.dev)
[![Windows](https://img.shields.io/badge/Platform-Windows-lightblue.svg)](https://windows.com)
[![GitHub](https://img.shields.io/badge/GitHub-multimedia--gesture--control-blue.svg)](https://github.com/ivangillig/multimedia-gesture-control)

*Sistema de control multimedia usando gestos de manos capturados por webcam*

**🌐 Repositorio Oficial:** [github.com/ivangillig/multimedia-gesture-control](https://github.com/ivangillig/multimedia-gesture-control)

[Características](#-características) • [Instalación](#-instalación) • [Uso](#-uso) • [Configuración](#️-configuración)

</div>

---

## ✨ Características

### 🔊 Control Inteligente de Volumen
- **Gesto**: Ambas manos en posición "cord grip" (como sujetando una cuerda)
- **Función**: La distancia entre las manos controla el volumen dinámicamente
- **Visual**: Línea verde conectando las manos con porcentaje en tiempo real
- **Rango**: 0% - 100% con mapeo suave y preciso

### ⏯️ Play/Pause Intuitivo
- **Gesto**: Secuencia palma abierta (1 seg) → cerrar puño
- **Función**: Alternar reproducción/pausa multimedia
- **Seguridad**: Confirmación visual y cooldown inteligente
- **Compatibilidad**: Funciona con cualquier reproductor multimedia

### 🎵 Navegación de Canciones Avanzada
- **Gesto**: Puño cerrado + inclinación de cabeza
- **Umbral**: ≥35° para activación (máxima precisión)
- **Funciones**:
  - 🠠 **Cabeza hacia la derecha**: Canción anterior
  - 🠢 **Cabeza hacia la izquierda**: Siguiente canción
- **Visual**: Transportador inteligente que aparece solo cuando se necesita
- **Feedback**: Indicador visual con colores (verde = listo, amarillo = inclinar más)

### 🛡️ Sistema de Seguridad Integrado
- **Detección inteligente**: Desactiva controles cuando las manos están cerca de la cara
- **Prevención de accidentes**: Evita activaciones involuntarias durante uso natural
- **Feedback visual**: Estado de bloqueo claramente indicado
- **Umbral configurable**: Distancia de 0.15 optimizada para seguridad

### 🎨 Interfaz Visual Moderna
- **Panel superior**: Estado del sistema, inclinación de cabeza, modo activo
- **Panel inferior**: Instrucciones claras y concisas
- **Indicadores dinámicos**: Aparecen solo cuando son relevantes
- **Diseño limpio**: Interfaz no intrusiva que no distrae

## 🚀 Instalación

### Requisitos del Sistema
- **OS**: Windows 10/11
- **Python**: 3.8 o superior
- **Webcam**: Cualquier cámara compatible
- **RAM**: Mínimo 4GB recomendado

### Instalación Rápida

```bash
# Clonar el repositorio oficial
git clone https://github.com/ivangillig/multimedia-gesture-control.git
cd multimedia-gesture-control

# Crear entorno virtual (recomendado)
python -m venv .venv
.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Dependencias

```bash
pip install opencv-python mediapipe pycaw comtypes numpy
```

## 🎯 Uso

### Inicio Rápido

```bash
python main.py
```

### 🎮 Controles y Gestos

| Gesto | Acción | Descripción Visual |
|-------|--------|-------------------|
| 🤏 **Dos manos "cord grip"** | Control de volumen | Línea verde con porcentaje |
| 🖐️➡️✊ **Palma → Puño** | Play/Pause | Secuencia de 1 segundo |
| ✊ + 🗣️↗️ **Puño + Cabeza derecha** | Canción anterior | Transportador verde ≥35° |
| ✊ + 🗣️↖️ **Puño + Cabeza izquierda** | Siguiente canción | Transportador verde ≥35° |
| **ESC** | Salir | Cierre seguro |

### 📊 Interfaz Visual

#### Panel Superior (Información del Sistema)
- **Inclinación**: Ángulo actual de la cabeza
- **Rostro**: Estado de detección facial
- **Modo**: Sistema activo (Volumen/Play/Multimedia/Inactivo)
- **Estado**: Bloqueado si manos cerca de la cara

#### Panel Inferior (Instrucciones)
- Controles disponibles en tiempo real
- Instrucciones claras y concisas

#### Indicadores Dinámicos
- **Transportador angular**: Solo visible con puño cerrado
- **Línea de volumen**: Solo activa durante control de volumen
- **Landmarks de manos**: Siempre visibles para feedback

## ⚙️ Configuración

### Archivo `config.py`

```python
class GestureConfig:
    # Detección de gestos
    MAX_HANDS = 2
    MEDIAPIPE_CONFIDENCE = 0.7
    
    # Timeouts y cooldowns
    PALM_HOLD_DURATION = 1.0  # Segundos para confirmar palma
    HEAD_TILT_TIMEOUT = 2.0   # Cooldown entre cambios de canción
    
    # Umbrales de seguridad
    FACE_TOUCH_THRESHOLD = 0.15  # Distancia mano-cara
    HEAD_TILT_THRESHOLD = 35     # Grados para navegación
    
    # Modos de operación
    MEDIA_GESTURE_MODE = "fist_head_tilt"  # Método preferido
    SHOW_DEBUG_INFO = True  # Información de depuración
```

## 📁 Estructura del Proyecto

```
controlmouse/
├── main.py                 # 🚀 Aplicación principal
├── gesture_detector.py     # 🤲 Detección y clasificación de gestos
├── volume_control.py       # 🔊 Control del volumen del sistema
├── media_control.py        # 🎵 Controles multimedia
├── config.py              # ⚙️ Configuración del sistema
├── requirements.txt       # 📦 Dependencias
└── README.md             # 📖 Documentación
```

## 🔧 Tecnologías

| Tecnología | Propósito | Versión |
|------------|-----------|---------|
| **OpenCV** | Procesamiento de video e imagen | 4.0+ |
| **MediaPipe** | Reconocimiento de manos y rostro | 0.10+ |
| **PyCaw** | Control de audio de Windows | Latest |
| **NumPy** | Cálculos matemáticos | 1.21+ |
| **Python** | Lenguaje principal | 3.8+ |

## 🎪 Características Avanzadas

### 🧠 Algoritmos Inteligentes
- **Detección facial**: 468 landmarks para precisión máxima
- **Reconocimiento de manos**: 21 puntos por mano con conexiones
- **Cálculos geométricos**: Ángulos y distancias en tiempo real
- **Filtrado de ruido**: Estabilización de gestos opcional

### 🎯 Precisión y Performance
- **FPS optimizado**: Procesamiento fluido en tiempo real
- **Baja latencia**: Respuesta instantánea a gestos
- **Memoria eficiente**: Uso optimizado de recursos
- **CPU balanceado**: Distribución inteligente de carga

### 🔐 Seguridad y Robustez
- **Validación de gestos**: Múltiples checkpoints por acción
- **Manejo de errores**: Recovery automático ante fallos
- **Estados seguros**: Desactivación preventiva de controles
- **Logging inteligente**: Información detallada para debugging

## 🚨 Troubleshooting

### Problemas Comunes

#### 🎥 Cámara no detectada
```bash
# Verificar dispositivos de video
python -c "import cv2; print(cv2.VideoCapture(0).read()[0])"
```

#### 🤲 Manos no reconocidas
- Asegurar buena iluminación
- Manos completamente visibles
- Fondo contrastante
- Distancia óptima: 50-150cm

#### 🔊 Audio no funciona
- Verificar permisos de Windows
- Ejecutar como administrador si es necesario
- Comprobar controladores de audio

#### ⚡ Performance lento
- Cerrar aplicaciones innecesarias
- Reducir resolución de cámara
- Ajustar `MEDIAPIPE_CONFIDENCE` en config

## 📈 Roadmap

- [ ] **Gestos personalizables**: Editor visual de gestos
- [ ] **Soporte multiplataforma**: Linux y macOS
- [ ] **Control por voz**: Comandos híbridos
- [ ] **Machine Learning**: Gestos adaptativos por usuario
- [ ] **API REST**: Control remoto desde otras aplicaciones
- [ ] **Profiles**: Configuraciones por aplicación

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor:

1. **Fork** el proyecto desde [github.com/ivangillig/multimedia-gesture-control](https://github.com/ivangillig/multimedia-gesture-control)
2. Crea una feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la branch (`git push origin feature/AmazingFeature`)
5. Abre un **Pull Request** en el repositorio oficial

Para más detalles, consulta [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 🤖 Desarrollo Asistido por IA

Este proyecto fue desarrollado usando **vibe coding** (desarrollo colaborativo asistido por inteligencia artificial). El concepto, diseño y iteraciones fueron guiados por el usuario, mientras que la implementación técnica fue asistida por AI para acelerar el proceso de desarrollo.

### Proceso de Desarrollo
- **Conceptualización**: Ideas y requisitos definidos por el usuario
- **Iteración continua**: Mejoras basadas en feedback en tiempo real
- **Implementación técnica**: Código generado y optimizado con asistencia de IA
- **Testing y refinamiento**: Pruebas y ajustes dirigidos por el usuario

## 🙏 Agradecimientos

- **MediaPipe Team** por el fantástico framework de ML
- **OpenCV Community** por las herramientas de visión computacional  
- **PyCaw** por la integración con el audio de Windows
- **GitHub Copilot/AI Assistants** por acelerar el proceso de desarrollo
- **Vibe Coding Community** por el enfoque colaborativo humano-IA

---

<div align="center">

**¿Te gustó el proyecto? ⭐ Dale una estrella en GitHub!**

*Desarrollado con 🤖 vibe coding - Colaboración humano-IA*

[⬆ Volver arriba](#-control-multimedia-con-reconocimiento-de-manos)

</div>
