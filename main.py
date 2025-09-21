import cv2
import mediapipe as mp
import time
from gesture_detector import GestureDetector
from volume_control import VolumeControl
from media_control import MediaControl
from config import GestureConfig

class HandController:
    def __init__(self):
        # Inicializar MediaPipe para manos
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False, 
            max_num_hands=GestureConfig.MAX_HANDS, 
            min_detection_confidence=GestureConfig.MEDIAPIPE_CONFIDENCE
        )
        
        # Inicializar MediaPipe para rostro
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.mp_draw = mp.solutions.drawing_utils
        
        # Inicializar componentes
        self.gesture_detector = GestureDetector()
        self.volume_control = VolumeControl()
        self.media_control = MediaControl()
        
        # Estados
        self.current_mode = "idle"  # idle, volume, play_pause, media
        self.last_gesture = None
        self.last_gesture_time = 0
        self.mode_cooldown = 0.5
        
        # Estados de play/pause
        self.pause_state = "waiting"  # waiting, palm_detected, ready_to_toggle
        self.pause_palm_time = 0
        self.palm_hold_duration = GestureConfig.PALM_HOLD_DURATION
        
        # Sistema de estabilización de gestos
        self.gesture_history = []
        self.stable_gesture_count = 0
        self.required_stable_frames = GestureConfig.STABLE_FRAMES_REQUIRED
        
        # Inicializar webcam
        print(f"🎥 Inicializando cámara {GestureConfig.CAMERA_INDEX}...")
        self.cap = cv2.VideoCapture(GestureConfig.CAMERA_INDEX)
        
        # Configurar resolución de la cámara
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, GestureConfig.CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, GestureConfig.CAMERA_HEIGHT)
            
            # Verificar resolución actual
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"📐 Resolución configurada: {actual_width}x{actual_height}")
        else:
            raise Exception("No se pudo inicializar la cámara")
            
        # Configurar ventana
        cv2.namedWindow('Control Multimedia con Manos', cv2.WINDOW_NORMAL)
        if GestureConfig.WINDOW_SCALE != 1.0:
            window_width = int(GestureConfig.CAMERA_WIDTH * GestureConfig.WINDOW_SCALE)
            window_height = int(GestureConfig.CAMERA_HEIGHT * GestureConfig.WINDOW_SCALE)
            cv2.resizeWindow('Control Multimedia con Manos', window_width, window_height)
            print(f"🖼️ Ventana redimensionada: {window_width}x{window_height}")

    def detect_gestures(self, hand_results, face_results):
        """Detectar gestos en ambas manos y rostro"""
        # Guardar face landmarks para dibujar después
        self.face_landmarks = None
        if face_results.multi_face_landmarks:
            self.face_landmarks = face_results.multi_face_landmarks[0]
            
        if not hand_results.multi_hand_landmarks or not hand_results.multi_handedness:
            return None, None, []
        
        # Obtener landmarks del rostro si están disponibles
        face_landmarks = None
        if face_results.multi_face_landmarks:
            face_landmarks = face_results.multi_face_landmarks[0]  # Usar la primera cara detectada
            
        hand_data = []
        for hand_landmarks, handedness in zip(hand_results.multi_hand_landmarks, hand_results.multi_handedness):
            hand_type = handedness.classification[0].label
            
            # Detectar gesto de puño con inclinación de cabeza
            is_fist_head_tilt, fist_head_direction = self.gesture_detector.is_fist_with_head_tilt(
                hand_landmarks, face_landmarks
            )
            
            # Verificar si la mano está tocando la cara (VALIDACIÓN DE SEGURIDAD)
            is_touching_face = self.gesture_detector.is_hand_touching_face(hand_landmarks, face_landmarks)
            
            hand_data.append({
                'type': hand_type,
                'landmarks': hand_landmarks,
                'is_palm': self.gesture_detector.is_palm_open(hand_landmarks),
                'is_fist': self.gesture_detector.is_fist(hand_landmarks),
                'is_cord': self.gesture_detector.is_cord_grip(hand_landmarks),
                'is_gun': self.gesture_detector.is_gun_gesture(hand_landmarks),
                'is_peace': self.gesture_detector.is_peace_sign(hand_landmarks),
                'is_fist_head_tilt': is_fist_head_tilt,
                'gun_direction': self.gesture_detector.get_gun_direction(hand_landmarks) if self.gesture_detector.is_gun_gesture(hand_landmarks) else None,
                'peace_direction': self.gesture_detector.get_peace_direction(hand_landmarks) if self.gesture_detector.is_peace_sign(hand_landmarks) else None,
                'fist_head_direction': fist_head_direction,
                'center': self.gesture_detector.get_hand_center(hand_landmarks),
                'is_touching_face': is_touching_face  # NUEVA VALIDACIÓN
            })
        
        # Separar manos izquierda y derecha
        left_hand = next((h for h in hand_data if h['type'] == 'Left'), None)
        right_hand = next((h for h in hand_data if h['type'] == 'Right'), None)
        
        return left_hand, right_hand, hand_data

    def process_volume_control(self, left_hand, right_hand):
        """Procesar control de volumen con ambas manos"""
        if left_hand and right_hand and left_hand['is_cord'] and right_hand['is_cord']:
            
            # VALIDACIÓN DE SEGURIDAD: No funcionar si cualquier mano está cerca de la cara
            if left_hand.get('is_touching_face') or right_hand.get('is_touching_face'):
                return False, None, None, None
                
            self.current_mode = "volume"
            
            # Calcular distancia entre manos
            distance = self.gesture_detector.calculate_distance(
                left_hand['center'], right_hand['center']
            )
            
            # Mapear a volumen
            volume = self.volume_control.map_distance_to_volume(distance)
            self.volume_control.set_volume(volume)
            
            return True, volume, left_hand['center'], right_hand['center']
        
        return False, None, None, None

    def process_play_pause_control(self, hand_data):
        """Procesar control de play/pause con secuencia palma->puño"""
        current_time = time.time()
        
        if hand_data and len(hand_data) == 1:  # Solo una mano visible
            hand = hand_data[0]
            
            # VALIDACIÓN DE SEGURIDAD: No funcionar si la mano está cerca de la cara
            if hand.get('is_touching_face'):
                self.pause_state = "waiting"  # Reset estado si toca la cara
                return False
            
            if self.pause_state == "waiting" and hand['is_palm']:
                self.pause_state = "palm_detected"
                self.pause_palm_time = current_time
                
            elif self.pause_state == "palm_detected":
                if hand['is_palm'] and (current_time - self.pause_palm_time) >= self.palm_hold_duration:
                    self.pause_state = "ready_to_toggle"
                elif hand['is_fist']:
                    self.pause_state = "waiting"  # Reset si cierra muy rápido
                elif not hand['is_palm']:
                    self.pause_state = "waiting"  # Reset si cambia gesto
                    
            elif self.pause_state == "ready_to_toggle" and hand['is_fist']:
                if self.media_control.play_pause():
                    self.pause_state = "waiting"
                    self.current_mode = "play_pause"
                    return True
                    
        else:
            self.pause_state = "waiting"
            
        return False

    def is_gesture_stable(self, gesture_type):
        """Verificar si un gesto es estable (se mantiene por varias frames)"""
        if not GestureConfig.REQUIRE_STABLE_GESTURE:
            return True
            
        # Agregar gesto actual al historial
        self.gesture_history.append(gesture_type)
        
        # Mantener solo las últimas N frames
        if len(self.gesture_history) > self.required_stable_frames:
            self.gesture_history.pop(0)
        
        # Verificar si las últimas N frames tienen el mismo gesto
        if len(self.gesture_history) >= self.required_stable_frames:
            return all(g == gesture_type for g in self.gesture_history)
        
        return False

    def process_media_control(self, hand_data):
        """Procesar controles multimedia con gesto mejorado y estabilización"""
        if hand_data and len(hand_data) == 1:  # Solo una mano visible
            hand = hand_data[0]
            
            # VALIDACIÓN DE SEGURIDAD: No funcionar si la mano está cerca de la cara
            if hand.get('is_touching_face'):
                self.gesture_history = []  # Reset historial si toca la cara
                return False, None
            
            # Determinar qué gesto usar según configuración
            current_gesture = None
            direction = None
            
            if GestureConfig.MEDIA_GESTURE_MODE == "fist_head_tilt" and hand['is_fist_head_tilt']:
                current_gesture = "fist_head_tilt"
                direction = hand['fist_head_direction']
            elif GestureConfig.MEDIA_GESTURE_MODE == "peace" and hand['is_peace']:
                current_gesture = "peace"
                direction = hand['peace_direction']
            elif GestureConfig.MEDIA_GESTURE_MODE == "gun" and hand['is_gun']:
                current_gesture = "gun"  
                direction = hand['gun_direction']
            
            # Para fist_head_tilt, no usar estabilización porque ya tiene timeout interno
            if current_gesture == "fist_head_tilt" and direction:
                self.current_mode = "media"
                print(f"🎯 Ejecutando gesto HEAD TILT: {current_gesture} hacia {direction}")
                
                if direction == "right":
                    if self.media_control.next_track():
                        print("✅ Siguiente canción ejecutada con HEAD TILT")
                        return True, f"next_{current_gesture}"
                    else:
                        print("❌ Error al ejecutar siguiente canción")
                elif direction == "left":
                    if self.media_control.previous_track():
                        print("✅ Canción anterior ejecutada con HEAD TILT")
                        return True, f"previous_{current_gesture}"
                    else:
                        print("❌ Error al ejecutar canción anterior")
            # Para otros gestos, usar estabilización
            elif current_gesture and direction and self.is_gesture_stable(current_gesture):
                self.current_mode = "media"
                print(f"🎯 Ejecutando gesto: {current_gesture} hacia {direction}")
                
                if direction == "right":
                    if self.media_control.next_track():
                        print("✅ Siguiente canción ejecutada")
                        return True, f"next_{current_gesture}"
                    else:
                        print("❌ Error al ejecutar siguiente canción")
                elif direction == "left":
                    if self.media_control.previous_track():
                        print("✅ Canción anterior ejecutada")
                        return True, f"previous_{current_gesture}"
                    else:
                        print("❌ Error al ejecutar canción anterior")
            else:
                # Reset si no hay gesto válido
                self.gesture_history = []
                        
        return False, None

    def draw_text_with_background(self, frame, text, position, font_scale=0.6, color=(255, 255, 255), thickness=1):
        """Dibujar texto con fondo negro para mejor visibilidad"""
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        x, y = position
        
        # Dibujar rectángulo negro de fondo
        cv2.rectangle(frame, (x - 5, y - text_size[1] - 5), 
                     (x + text_size[0] + 5, y + 5), (0, 0, 0), -1)
        
        # Dibujar texto blanco encima
        cv2.putText(frame, text, position, font, font_scale, color, thickness)

    def draw_info_panel(self, frame):
        """Dibujar panel de información en la esquina superior izquierda"""
        h, w, _ = frame.shape
        
        # Información a mostrar
        info_lines = []
        
        # Siempre mostrar grado de inclinación
        if hasattr(self.gesture_detector, 'last_head_angle'):
            angle = self.gesture_detector.last_head_angle
            info_lines.append(f"Inclinacion: {angle:.1f}°")
        else:
            info_lines.append("Inclinacion: --")
        
        # Estado de detección
        if hasattr(self, 'face_landmarks') and self.face_landmarks:
            info_lines.append("Rostro: Detectado")
        else:
            info_lines.append("Rostro: No detectado")
        
        # NUEVA: Validación de mano-cara
        hand_touching_face = False
        if hasattr(self, 'current_hand_data') and self.current_hand_data:
            for hand in self.current_hand_data:
                if hand.get('is_touching_face'):
                    hand_touching_face = True
                    break
        
        if hand_touching_face:
            info_lines.append("Estado: BLOQUEADO - Mano cerca cara")
        else:
            # Estado actual del sistema
            mode_text = {
                "idle": "Modo: Inactivo",
                "volume": "Modo: Volumen", 
                "play_pause": "Modo: Play/Pause",
                "media": "Modo: Multimedia"
            }
            info_lines.append(mode_text.get(self.current_mode, "Modo: Desconocido"))
        
        # Calcular tamaño del panel
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.4
        thickness = 1
        line_height = 18
        padding = 8
        
        max_width = 0
        for line in info_lines:
            text_size = cv2.getTextSize(line, font, font_scale, thickness)[0]
            max_width = max(max_width, text_size[0])
        
        # Posición del panel (esquina superior izquierda)
        panel_x = 10
        panel_y = 10
        panel_width = max_width + padding * 2
        panel_height = len(info_lines) * line_height + padding * 2
        
        # Dibujar rectángulo de fondo (gris oscuro)
        cv2.rectangle(frame, (panel_x, panel_y), 
                     (panel_x + panel_width, panel_y + panel_height), (40, 40, 40), -1)
        
        # Dibujar borde
        cv2.rectangle(frame, (panel_x, panel_y), 
                     (panel_x + panel_width, panel_y + panel_height), (100, 100, 100), 1)
        
        # Dibujar cada línea de información
        for i, line in enumerate(info_lines):
            text_y = panel_y + padding + (i + 1) * line_height - 3
            # Color rojo si está bloqueado, verde normal si no
            color = (100, 100, 255) if "BLOQUEADO" in line else (150, 255, 150)  # Rojo claro o verde claro
            cv2.putText(frame, line, (panel_x + padding, text_y), 
                       font, font_scale, color, thickness)

    def draw_instructions_panel(self, frame):
        """Dibujar panel de instrucciones con el mismo estilo del panel superior"""
        h, w, _ = frame.shape
        
        # Instrucciones sin caracteres especiales
        instructions = [
            "Dos manos abiertas: Control volumen",
            "Palma a Puno: Play/Pause", 
            "Puno + cabeza inclinada 35 grados: Cambiar cancion",
            "Q: Salir"
        ]
        
        # Calcular tamaño del rectángulo necesario (mismo estilo que panel superior)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.4  # Mismo tamaño que panel superior
        thickness = 1
        line_height = 18
        padding = 8
        
        max_width = 0
        for instruction in instructions:
            text_size = cv2.getTextSize(instruction, font, font_scale, thickness)[0]
            max_width = max(max_width, text_size[0])
        
        # Posición del panel
        panel_x = 20
        panel_y = h - 100
        panel_width = max_width + padding * 2
        panel_height = len(instructions) * line_height + padding * 2
        
        # Dibujar rectángulo de fondo (mismo gris oscuro que panel superior)
        cv2.rectangle(frame, (panel_x, panel_y), 
                     (panel_x + panel_width, panel_y + panel_height), (40, 40, 40), -1)
        
        # Dibujar borde (mismo que panel superior)
        cv2.rectangle(frame, (panel_x, panel_y), 
                     (panel_x + panel_width, panel_y + panel_height), (100, 100, 100), 1)
        
        # Dibujar cada instrucción (mismo color verde claro que panel superior)
        for i, instruction in enumerate(instructions):
            text_y = panel_y + padding + (i + 1) * line_height - 3
            cv2.putText(frame, instruction, (panel_x + padding, text_y), 
                       font, font_scale, (150, 255, 150), thickness)  # Verde claro igual que panel superior
        """Dibujar panel de instrucciones en un solo rectángulo"""
        h, w, _ = frame.shape
        
        # Instrucciones sin caracteres especiales
        instructions = [
            "Dos manos abiertas: Control volumen",
            "Palma a Puno: Play/Pause", 
            "Puno + cabeza inclinada 35 grados: Cambiar cancion",
            "Q: Salir"
        ]
        
        # Calcular tamaño del rectángulo necesario
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        line_height = 20
        padding = 10
        
        max_width = 0
        for instruction in instructions:
            text_size = cv2.getTextSize(instruction, font, font_scale, thickness)[0]
            max_width = max(max_width, text_size[0])
        
        # Posición del panel
        panel_x = 20
        panel_y = h - 120
        panel_width = max_width + padding * 2
        panel_height = len(instructions) * line_height + padding * 2
        
        # Dibujar rectángulo negro de fondo para todo el panel
        cv2.rectangle(frame, (panel_x - 5, panel_y - 5), 
                     (panel_x + panel_width, panel_y + panel_height), (40, 40, 40), -1)
        
        # Dibujar cada instrucción
        for i, instruction in enumerate(instructions):
            text_y = panel_y + padding + (i + 1) * line_height
            cv2.putText(frame, instruction, (panel_x + padding, text_y), 
                       font, font_scale, (150, 255, 150), thickness)

    def draw_ui(self, frame, left_hand, right_hand, hand_data):
        """Dibujar interfaz de usuario"""
        h, w, _ = frame.shape
        
        # Verificar si hay algún puño activo (para mostrar indicador de ángulo)
        show_angle_indicator = False
        if hand_data:
            for hand in hand_data:
                if hand.get('is_fist') and not hand.get('is_touching_face'):
                    show_angle_indicator = True
                    break
        
        # Dibujar indicador de ángulo SOLO cuando hay puño cerrado y no toca la cara
        if show_angle_indicator and hasattr(self, 'face_landmarks') and self.face_landmarks:
            # Obtener puntos clave para calcular el ángulo
            left_eye = self.face_landmarks.landmark[33]  # Comisura externa ojo izquierdo
            right_eye = self.face_landmarks.landmark[263]  # Comisura externa ojo derecho
            
            # Convertir a coordenadas de píxeles
            left_eye_px = (int(left_eye.x * w), int(left_eye.y * h))
            right_eye_px = (int(right_eye.x * w), int(right_eye.y * h))
            
            # Calcular punto medio entre los ojos
            center_x = (left_eye_px[0] + right_eye_px[0]) // 2
            center_y = (left_eye_px[1] + right_eye_px[1]) // 2
            center_point = (center_x, center_y)
            
            # Dibujar línea horizontal de referencia (0 grados)
            reference_length = 80
            ref_start = (center_x - reference_length, center_y)
            ref_end = (center_x + reference_length, center_y)
            cv2.line(frame, ref_start, ref_end, (100, 100, 100), 1)  # Línea gris de referencia
            
            # Dibujar línea que representa el ángulo actual
            if hasattr(self.gesture_detector, 'last_head_angle'):
                import math
                angle_rad = math.radians(-self.gesture_detector.last_head_angle)  # Negativo para que coincida visualmente
                
                # Calcular punto final de la línea del ángulo
                angle_length = 60
                end_x = center_x + int(angle_length * math.cos(angle_rad))
                end_y = center_y + int(angle_length * math.sin(angle_rad))
                angle_end = (end_x, end_y)
                
                # Color de la línea según el ángulo (verde si está en rango de detección)
                abs_angle = abs(self.gesture_detector.last_head_angle)
                if abs_angle >= 35:  # Umbral de detección
                    line_color = (0, 255, 0)  # Verde - en rango de detección
                else:
                    line_color = (0, 255, 255)  # Amarillo - fuera de rango
                
                # Dibujar línea del ángulo
                cv2.line(frame, center_point, angle_end, line_color, 3)
                
                # Dibujar punto central
                cv2.circle(frame, center_point, 4, (255, 255, 255), -1)
                
                # Mostrar ángulo en texto cerca de la línea
                angle_text = f"{self.gesture_detector.last_head_angle:.1f}°"
                text_pos = (center_x + 25, center_y - 15)
                cv2.putText(frame, angle_text, text_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.5, line_color, 2)
        
        # Dibujar landmarks de las manos
        if left_hand:
            self.mp_draw.draw_landmarks(
                frame, left_hand['landmarks'], self.mp_hands.HAND_CONNECTIONS
            )
        if right_hand:
            self.mp_draw.draw_landmarks(
                frame, right_hand['landmarks'], self.mp_hands.HAND_CONNECTIONS
            )
        
        # UI según el modo actual - SOLO para control de volumen
        if self.current_mode == "volume":
            # Dibujar barra de volumen
            volume_active, volume, left_center, right_center = self.process_volume_control(left_hand, right_hand)
            if volume_active:
                bar_x1 = int(left_center[0] * w)
                bar_y1 = int(left_center[1] * h)
                bar_x2 = int(right_center[0] * w)
                bar_y2 = int(right_center[1] * h)
                
                cv2.line(frame, (bar_x1, bar_y1), (bar_x2, bar_y2), (0, 255, 0), 5)
                cv2.circle(frame, (bar_x1, bar_y1), 10, (255, 0, 0), -1)
                cv2.circle(frame, (bar_x2, bar_y2), 10, (255, 0, 0), -1)
                
                # Mostrar volumen sobre la línea entre las manos
                vol_text = f'{volume}%'
                text_size = cv2.getTextSize(vol_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
                # Calcular el punto medio de la línea
                mid_x = (bar_x1 + bar_x2) // 2
                mid_y = (bar_y1 + bar_y2) // 2
                # Posicionar el texto encima de la línea
                text_x = mid_x - text_size[0] // 2
                text_y = mid_y - 20  # 20 píxeles arriba de la línea
                self.draw_text_with_background(frame, vol_text, (text_x, text_y), 0.8, (255, 255, 255), 2)
        
        # Panel de información superior izquierda
        self.draw_info_panel(frame)
        
        # Panel de instrucciones agrupado en la parte inferior
        self.draw_instructions_panel(frame)

    def run(self):
        """Bucle principal"""
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
                
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb)
            face_results = self.face_mesh.process(rgb)
            
            # Detectar gestos
            left_hand, right_hand, hand_data = self.detect_gestures(results, face_results)
            
            # Asegurar que hand_data nunca sea None
            if hand_data is None:
                hand_data = []
            
            # Guardar hand_data para el panel de información
            self.current_hand_data = hand_data
            
            # Reset mode si no hay gestos activos
            current_time = time.time()
            if (current_time - self.last_gesture_time) > self.mode_cooldown:
                if self.current_mode not in ["play_pause"]:  # Mantener estado de play_pause
                    self.current_mode = "idle"
            
            # Procesar controles
            volume_active, _, _, _ = self.process_volume_control(left_hand, right_hand)
            play_pause_toggled = self.process_play_pause_control(hand_data)
            media_active, media_action = self.process_media_control(hand_data)
            
            # Debug: mostrar cuando se activan controles
            if GestureConfig.SHOW_DEBUG_INFO:
                if volume_active:
                    print("✅ Control de volumen activo")
                if play_pause_toggled:
                    print("✅ Play/Pause activado")
                if media_active:
                    print(f"✅ Control multimedia: {media_action}")
            
            if volume_active or play_pause_toggled or media_active:
                self.last_gesture_time = current_time
            
            # Dibujar UI
            self.draw_ui(frame, left_hand, right_hand, hand_data)
            
            cv2.imshow('Control Multimedia con Manos', frame)
            if cv2.waitKey(1) & 0xFF == 27:  # ESC para salir
                break
        
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    controller = HandController()
    try:
        controller.run()
    except KeyboardInterrupt:
        print("\n🔴 Programa cerrado por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
    finally:
        print("✅ Recursos liberados correctamente")
