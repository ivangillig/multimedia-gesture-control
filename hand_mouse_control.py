import cv2
import mediapipe as mp
import numpy as np
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER
import math

# Inicializar MediaPipe Hands
dashands = mp.solutions.hands
hands = dashands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Inicializar control de volumen de Windows
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

# Obtener rango de volumen
vol_range = volume.GetVolumeRange()
min_vol = vol_range[0]
max_vol = vol_range[1]

# Inicializar webcam
cap = cv2.VideoCapture(0)

# Función para detectar posición de "cordón" con 3 dedos
def is_cord_grip(hand_landmarks):
    # Verificar que pulgar, índice y medio estén extendidos
    thumb_tip = hand_landmarks.landmark[dashands.HandLandmark.THUMB_TIP]
    thumb_ip = hand_landmarks.landmark[dashands.HandLandmark.THUMB_IP]
    index_tip = hand_landmarks.landmark[dashands.HandLandmark.INDEX_FINGER_TIP]
    index_pip = hand_landmarks.landmark[dashands.HandLandmark.INDEX_FINGER_PIP]
    middle_tip = hand_landmarks.landmark[dashands.HandLandmark.MIDDLE_FINGER_TIP]
    middle_pip = hand_landmarks.landmark[dashands.HandLandmark.MIDDLE_FINGER_PIP]
    
    # Anular y meñique doblados
    ring_tip = hand_landmarks.landmark[dashands.HandLandmark.RING_FINGER_TIP]
    ring_pip = hand_landmarks.landmark[dashands.HandLandmark.RING_FINGER_PIP]
    pinky_tip = hand_landmarks.landmark[dashands.HandLandmark.PINKY_TIP]
    pinky_pip = hand_landmarks.landmark[dashands.HandLandmark.PINKY_PIP]
    
    # Verificar dedos extendidos (pulgar, índice, medio)
    extended_fingers = 0
    if index_tip.y < index_pip.y:
        extended_fingers += 1
    if middle_tip.y < middle_pip.y:
        extended_fingers += 1
    if abs(thumb_tip.x - thumb_ip.x) > 0.04:
        extended_fingers += 1
    
    # Verificar dedos doblados (anular, meñique)
    folded_fingers = 0
    if ring_tip.y > ring_pip.y:
        folded_fingers += 1
    if pinky_tip.y > pinky_pip.y:
        folded_fingers += 1
    
    return extended_fingers >= 2 and folded_fingers >= 1

def get_hand_center(hand_landmarks):
    # Punto medio entre índice y medio
    index_tip = hand_landmarks.landmark[dashands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = hand_landmarks.landmark[dashands.HandLandmark.MIDDLE_FINGER_TIP]
    center_x = (index_tip.x + middle_tip.x) / 2
    center_y = (index_tip.y + middle_tip.y) / 2
    return center_x, center_y

def calculate_distance(point1, point2):
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def map_distance_to_volume(distance, min_dist=0.05, max_dist=0.8):
    # Mapear distancia a volumen (0-100)
    if distance < min_dist:
        distance = min_dist
    if distance > max_dist:
        distance = max_dist
    
    volume_percent = ((distance - min_dist) / (max_dist - min_dist)) * 100
    return int(volume_percent)

def set_volume(vol_percent):
    # Convertir porcentaje a rango de Windows
    vol_db = min_vol + (vol_percent / 100) * (max_vol - min_vol)
    volume.SetMasterVolumeLevel(vol_db, None)

# Estado del control de volumen
volume_active = False
current_volume = 50

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    hand_types = []
    hand_landmarks_list = []
    if results.multi_hand_landmarks and results.multi_handedness:
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            hand_types.append(handedness.classification[0].label)  # 'Left' o 'Right'
            hand_landmarks_list.append(hand_landmarks)
            mp_draw.draw_landmarks(frame, hand_landmarks, dashands.HAND_CONNECTIONS)

    # Lógica de control de volumen
    if len(hand_types) == 2:
        try:
            idx_right = hand_types.index('Right')
            idx_left = hand_types.index('Left')
        except ValueError:
            idx_right, idx_left = 0, 1  # fallback
        
        right_hand = hand_landmarks_list[idx_right]
        left_hand = hand_landmarks_list[idx_left]
        
        # Verificar si ambas manos están en posición de "cordón"
        if is_cord_grip(right_hand) and is_cord_grip(left_hand):
            volume_active = True
            
            # Obtener centros de las manos
            right_center = get_hand_center(right_hand)
            left_center = get_hand_center(left_hand)
            
            # Calcular distancia entre las manos
            distance = calculate_distance(right_center, left_center)
            
            # Mapear distancia a volumen
            current_volume = map_distance_to_volume(distance)
            set_volume(current_volume)
            
            # Dibujar barra de volumen
            bar_x1 = int(left_center[0] * w)
            bar_y1 = int(left_center[1] * h)
            bar_x2 = int(right_center[0] * w)
            bar_y2 = int(right_center[1] * h)
            
            # Línea del "cordón"
            cv2.line(frame, (bar_x1, bar_y1), (bar_x2, bar_y2), (0, 255, 0), 5)
            
            # Círculos en los extremos
            cv2.circle(frame, (bar_x1, bar_y1), 10, (255, 0, 0), -1)
            cv2.circle(frame, (bar_x2, bar_y2), 10, (255, 0, 0), -1)
            
            # Mostrar volumen actual
            cv2.putText(frame, f'Volumen: {current_volume}%', (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        else:
            volume_active = False
    else:
        volume_active = False

    # Mostrar instrucciones
    if not volume_active:
        cv2.putText(frame, 'Usa 3 dedos (pulgar, indice, medio) en ambas manos', (50, h-60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(frame, 'para controlar el volumen', (50, h-30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    cv2.imshow('Control de Volumen con Manos', frame)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC para salir
        break

cap.release()
cv2.destroyAllWindows()
