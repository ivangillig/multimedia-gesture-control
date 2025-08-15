import mediapipe as mp
import math
import time

class GestureDetector:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        
        # Timeout para evitar detecciones múltiples de inclinación de cabeza
        self.last_head_tilt_time = 0
        self.head_tilt_cooldown = 1.5  # 1.5 segundos entre detecciones
        
        # Control de logging para toque de cara
        self.face_touch_logged = False  # Para evitar spam de logs
        
    def is_palm_open(self, hand_landmarks):
        """Detectar palma abierta"""
        thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        thumb_ip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_IP]
        
        fingers = [
            (hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP], 
             hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_PIP]),
            (hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP], 
             hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP]),
            (hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_TIP], 
             hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_PIP]),
            (hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP], 
             hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_PIP]),
        ]
        
        open_fingers = 0
        for tip, pip in fingers:
            if tip.y < pip.y:
                open_fingers += 1
        
        if abs(thumb_tip.x - thumb_ip.x) > 0.04:
            open_fingers += 1
            
        return open_fingers >= 4

    def is_fist(self, hand_landmarks):
        """Detectar puño cerrado - MÁS ESTRICTO para evitar falsas detecciones"""
        thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        thumb_ip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_IP]
        
        fingers = [
            (hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP], 
             hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_PIP]),
            (hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP], 
             hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP]),
            (hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_TIP], 
             hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_PIP]),
            (hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP], 
             hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_PIP]),
        ]
        
        # TODOS los dedos deben estar claramente doblados (más estricto)
        closed_fingers = 0
        for tip, pip in fingers:
            # Aumentar el umbral para requerir que esté MÁS doblado
            if tip.y > (pip.y + 0.02):  # Más estricto: 0.02 en lugar de 0
                closed_fingers += 1
                
        # El pulgar también debe estar doblado o pegado
        thumb_folded = abs(thumb_tip.x - thumb_ip.x) < 0.03  # Pulgar no extendido
        
        # Requerir TODOS los 4 dedos + pulgar para un puño más estricto
        return closed_fingers == 4 and thumb_folded

    def is_cord_grip(self, hand_landmarks):
        """Detectar posición de cordón - solo índice y medio extendidos como pinzas"""
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        index_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_PIP]
        middle_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        middle_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
        
        # Otros dedos doblados
        ring_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_TIP]
        ring_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_PIP]
        pinky_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
        pinky_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_PIP]
        thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        thumb_ip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_IP]
        
        # Índice y medio extendidos
        extended_fingers = 0
        if index_tip.y < index_pip.y:
            extended_fingers += 1
        if middle_tip.y < middle_pip.y:
            extended_fingers += 1
        
        # Otros dedos doblados (incluyendo pulgar)
        folded_fingers = 0
        if ring_tip.y > ring_pip.y:
            folded_fingers += 1
        if pinky_tip.y > pinky_pip.y:
            folded_fingers += 1
        if abs(thumb_tip.x - thumb_ip.x) < 0.03:  # Pulgar pegado
            folded_fingers += 1
        
        return extended_fingers == 2 and folded_fingers >= 2

    def is_gun_gesture(self, hand_landmarks):
        """Detectar gesto de pistola más estricto (índice + pulgar extendidos, otros doblados)"""
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        index_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_PIP]
        
        thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        thumb_ip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_IP]
        
        middle_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        middle_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
        ring_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_TIP]
        ring_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_PIP]
        pinky_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
        pinky_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_PIP]
        wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
        
        # Requisitos estrictos para pistola real:
        
        # 1. Índice claramente extendido
        index_extended = index_tip.y < (index_pip.y - 0.04)
        
        # 2. Pulgar claramente extendido hacia arriba (OBLIGATORIO)
        thumb_extended = thumb_tip.y < (thumb_ip.y - 0.04)
        
        # 3. Los otros 3 dedos TODOS doblados (sin excepciones)
        middle_folded = middle_tip.y > (middle_pip.y + 0.03)
        ring_folded = ring_tip.y > (ring_pip.y + 0.03)
        pinky_folded = pinky_tip.y > (pinky_pip.y + 0.03)
        all_others_folded = middle_folded and ring_folded and pinky_folded
        
        # 4. Orientación: la mano debe estar relativamente horizontal
        # El índice no debe estar apuntando muy arriba o muy abajo
        horizontal_pointing = abs(index_tip.y - wrist.y) < 0.12
        
        # 5. El índice debe estar claramente separado del pulgar
        finger_separation = abs(index_tip.x - thumb_tip.x) > 0.05
        
        # TODOS los requisitos deben cumplirse
        return (index_extended and thumb_extended and all_others_folded and 
                horizontal_pointing and finger_separation)

    def is_peace_sign(self, hand_landmarks):
        """Detectar gesto de paz (índice y medio extendidos, otros doblados) - alternativa más estable"""
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        index_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_PIP]
        middle_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        middle_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
        
        ring_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_TIP]
        ring_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_PIP]
        pinky_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
        pinky_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_PIP]
        thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        thumb_ip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_IP]
        
        # Índice y medio extendidos
        index_extended = index_tip.y < index_pip.y
        middle_extended = middle_tip.y < middle_pip.y
        
        # Otros dedos doblados
        ring_folded = ring_tip.y > ring_pip.y
        pinky_folded = pinky_tip.y > pinky_pip.y
        thumb_folded = abs(thumb_tip.x - thumb_ip.x) < 0.03  # Pulgar pegado
        
        return (index_extended and middle_extended and 
                ring_folded and pinky_folded and thumb_folded)

    def get_gun_direction(self, hand_landmarks):
        """Determinar dirección de la pistola (izquierda/derecha)"""
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
        
        if index_tip.x > wrist.x:
            return "right"  # Apuntando a la derecha
        else:
            return "left"   # Apuntando a la izquierda

    def detect_head_tilt(self, face_landmarks):
        """Detectar inclinación de la cabeza usando landmarks del rostro"""
        if not face_landmarks:
            return None
            
        # Verificar timeout para evitar múltiples detecciones
        current_time = time.time()
        if current_time - self.last_head_tilt_time < self.head_tilt_cooldown:
            return None
        
        # Puntos clave del rostro para detectar inclinación
        # Usar puntos de los ojos y la nariz
        left_eye = face_landmarks.landmark[33]   # Esquina izquierda del ojo izquierdo
        right_eye = face_landmarks.landmark[263] # Esquina derecha del ojo derecho
        nose_tip = face_landmarks.landmark[1]    # Punta de la nariz
        
        # Calcular la línea de los ojos
        eye_line_slope = (right_eye.y - left_eye.y) / (right_eye.x - left_eye.x + 0.0001)
        
        # Convertir pendiente a ángulo
        angle_rad = math.atan(eye_line_slope)
        angle_deg = math.degrees(angle_rad)
        
        # Guardar el ángulo para mostrarlo en la UI
        self.last_head_angle = angle_deg
        
        # Umbral para detectar inclinación (en grados) - AUMENTADO a 35°
        tilt_threshold = 35  # grados (aumentado para requerir inclinación más intencional)
        
        if angle_deg > tilt_threshold:
            self.last_head_tilt_time = current_time  # Actualizar timeout
            print(f"🎵➡️ SIGUIENTE CANCIÓN - Cabeza inclinada IZQUIERDA ({angle_deg:.1f}°)")
            return "right"   # Cabeza inclinada hacia la izquierda = siguiente canción
        elif angle_deg < -tilt_threshold:
            self.last_head_tilt_time = current_time  # Actualizar timeout
            print(f"🎵⬅️ CANCIÓN ANTERIOR - Cabeza inclinada DERECHA ({angle_deg:.1f}°)")
            return "left"  # Cabeza inclinada hacia la derecha = canción anterior
        else:
            return None     # Sin inclinación suficiente

    def is_fist_with_head_tilt(self, hand_landmarks, face_landmarks=None):
        """Detectar puño cerrado con inclinación de cabeza"""
        # Primero verificar que es un puño
        if not self.is_fist(hand_landmarks):
            return False, None
        
        # Detectar inclinación de la cabeza
        if face_landmarks is None:
            return False, None
        
        head_tilt = self.detect_head_tilt(face_landmarks)
        
        if head_tilt:
            return True, head_tilt
        else:
            return False, None

    def get_peace_direction(self, hand_landmarks):
        """Determinar dirección del signo de paz basado en orientación de la mano"""
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        middle_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
        
        # Punto medio entre índice y medio
        fingers_center_x = (index_tip.x + middle_tip.x) / 2
        
        # Si los dedos están más a la derecha que la muñeca = derecha
        if fingers_center_x > wrist.x:
            return "right"
        else:
            return "left"

    def get_hand_center(self, hand_landmarks):
        """Obtener centro de la mano entre índice y medio"""
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        middle_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        center_x = (index_tip.x + middle_tip.x) / 2
        center_y = (index_tip.y + middle_tip.y) / 2
        return center_x, center_y

    def is_hand_touching_face(self, hand_landmarks, face_landmarks):
        """Detectar si la mano está tocando o muy cerca de la cara"""
        if not face_landmarks:
            return False
            
        # Obtener puntos clave de la mano
        hand_center = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
        wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
        
        # Obtener puntos clave de la cara (contorno facial)
        face_points = [
            face_landmarks.landmark[10],   # Frente
            face_landmarks.landmark[152],  # Barbilla
            face_landmarks.landmark[234],  # Mejilla izquierda 
            face_landmarks.landmark[454],  # Mejilla derecha
            face_landmarks.landmark[1],    # Nariz
        ]
        
        # Calcular distancia mínima entre la mano y la cara
        min_distance = float('inf')
        
        for face_point in face_points:
            # Distancia del centro de la mano a puntos de la cara
            distance_center = math.sqrt(
                (hand_center.x - face_point.x)**2 + 
                (hand_center.y - face_point.y)**2
            )
            
            # Distancia de la muñeca a puntos de la cara
            distance_wrist = math.sqrt(
                (wrist.x - face_point.x)**2 + 
                (wrist.y - face_point.y)**2
            )
            
            min_distance = min(min_distance, distance_center, distance_wrist)
        
        # Si la distancia es menor a este umbral, consideramos que está tocando la cara
        touch_threshold = 0.15  # Ajustable según sea necesario
        
        is_touching = min_distance < touch_threshold
        
        # Debug: mostrar estado actual
        #print(f"DEBUG: is_touching={is_touching}, face_touch_logged={self.face_touch_logged}, distance={min_distance:.3f}")
        
        if is_touching:
            if not self.face_touch_logged:
                # Mostrar mensaje solo la primera vez que se detecta
                print(f"⚠️ MANO CERCA DE LA CARA - Distancia: {min_distance:.3f} - CONTROLES DESHABILITADOS")
                self.face_touch_logged = True
        else:
            if self.face_touch_logged:
                # Mostrar mensaje cuando se libera la mano de la cara
                print(f"✅ MANO LIBERADA - Distancia: {min_distance:.3f} - CONTROLES REACTIVADOS")
                self.face_touch_logged = False
            
        return is_touching

    def calculate_distance(self, point1, point2):
        """Calcular distancia euclidiana entre dos puntos"""
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
