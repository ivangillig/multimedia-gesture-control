"""
Configuración del sistema de control por gestos
Ajusta estos valores para cambiar la sensibilidad y comportamiento
"""

class GestureConfig:
    # Sensibilidad de detección de gestos (0.0 - 1.0, menor = más estricto)
    GESTURE_SENSITIVITY = 0.7
    
    # Tiempo mínimo entre activaciones de gestos multimedia (segundos)
    MEDIA_COOLDOWN = 2.0  # Aumentado más para evitar activaciones accidentales
    
    # Tiempo mínimo para mantener palma abierta antes de poder hacer play/pause
    PALM_HOLD_DURATION = 0.5  # Aumentado para evitar falsos positivos
    
    # Distancia mínima y máxima para control de volumen
    VOLUME_MIN_DISTANCE = 0.08  # Volumen mínimo (manos muy juntas)
    VOLUME_MAX_DISTANCE = 0.7   # Volumen máximo (manos separadas)
    
    # Configuración de detección de MediaPipe
    MEDIAPIPE_CONFIDENCE = 0.8  # Aumentado para mejor detección
    MAX_HANDS = 2
    
    # Configuración de cámara
    CAMERA_INDEX = 1  # 0=cámara integrada, 1=cámara USB externa, 2=segunda externa, etc.
    
    # Configuración de resolución y ventana
    CAMERA_WIDTH = 1280   # Ancho de la cámara (640, 1280, 1920)
    CAMERA_HEIGHT = 720   # Alto de la cámara (480, 720, 1080)
    WINDOW_SCALE = 1.0    # Factor de escala de la ventana (1.0 = tamaño original, 1.5 = 150%)
    
    # Modo de control multimedia preferido
    MEDIA_GESTURE_MODE = "fist_head_tilt"  # "gun", "peace", o "fist_head_tilt"
    
    # Filtros adicionales para evitar falsos positivos
    REQUIRE_STABLE_GESTURE = True  # Reactivado para evitar falsos positivos
    STABLE_FRAMES_REQUIRED = 5     # Aumentado: requiere 5 frames consecutivos
    
    # Debug
    SHOW_DEBUG_INFO = True  # Mostrar información de debug en consola
