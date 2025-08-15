import cv2
import mediapipe as mp
from gesture_detector import GestureDetector

def debug_gestures():
    """Script para debugear la detección de gestos en tiempo real"""
    
    # Inicializar MediaPipe
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False, 
        max_num_hands=1,  # Solo una mano para simplificar
        min_detection_confidence=0.7
    )
    mp_draw = mp.solutions.drawing_utils
    
    # Inicializar detector
    gesture_detector = GestureDetector()
    
    # Inicializar webcam
    cap = cv2.VideoCapture(0)
    
    print("🔧 Script de debug - Detección de gestos")
    print("Muestra una mano a la cámara y ve qué gestos detecta")
    print("ESC para salir")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Dibujar landmarks
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                # Detectar todos los gestos
                is_palm = gesture_detector.is_palm_open(hand_landmarks)
                is_fist = gesture_detector.is_fist(hand_landmarks)
                is_cord = gesture_detector.is_cord_grip(hand_landmarks)
                is_gun = gesture_detector.is_gun_gesture(hand_landmarks)
                is_peace = gesture_detector.is_peace_sign(hand_landmarks)
                is_fist_tilt, fist_tilt_dir = gesture_detector.is_fist_with_tilt(hand_landmarks)
                
                # Mostrar información
                y_pos = 30
                gestures_detected = []
                
                if is_palm:
                    gestures_detected.append("PALMA")
                if is_fist:
                    gestures_detected.append("PUÑO")
                if is_cord:
                    gestures_detected.append("CORDÓN")
                if is_gun:
                    gestures_detected.append("PISTOLA")
                    gun_dir = gesture_detector.get_gun_direction(hand_landmarks)
                    gestures_detected.append(f"DIR: {gun_dir}")
                if is_peace:
                    gestures_detected.append("PAZ")
                    peace_dir = gesture_detector.get_peace_direction(hand_landmarks)
                    gestures_detected.append(f"PAZ_DIR: {peace_dir}")
                if is_fist_tilt:
                    gestures_detected.append("PUÑO_INCLINADO")
                    gestures_detected.append(f"INCL_DIR: {fist_tilt_dir}")
                
                if gestures_detected:
                    gesture_text = " | ".join(gestures_detected)
                    cv2.putText(frame, gesture_text, (10, y_pos), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    cv2.putText(frame, "SIN GESTO DETECTADO", (10, y_pos), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Información detallada para puño inclinado
                if is_fist_tilt:
                    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
                    middle_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
                    pinky_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_MCP]
                    index_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP]
                    
                    lateral_vector_y = pinky_mcp.y - index_mcp.y
                    
                    debug_info = f"Inclinacion lateral: {lateral_vector_y:.3f} (>0.05=der, <-0.05=izq)"
                    cv2.putText(frame, debug_info, (10, y_pos + 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                
                # Información detallada para pistola
                elif is_gun:
                    # Obtener coordenadas específicas
                    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    index_pip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP]
                    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                    thumb_ip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_IP]
                    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
                    
                    # Calcular métricas
                    index_ext = index_tip.y < (index_pip.y - 0.04)
                    thumb_ext = thumb_tip.y < (thumb_ip.y - 0.04)
                    horizontal = abs(index_tip.y - wrist.y) < 0.12
                    separation = abs(index_tip.x - thumb_tip.x) > 0.05
                    
                    debug_info = f"Idx:{index_ext} Thumb:{thumb_ext} Horiz:{horizontal} Sep:{separation}"
                    cv2.putText(frame, debug_info, (10, y_pos + 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                    
                    # Mostrar valores numéricos
                    values = f"IdxY:{index_tip.y:.2f} ThumbY:{thumb_tip.y:.2f} WristY:{wrist.y:.2f}"
                    cv2.putText(frame, values, (10, y_pos + 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
                else:
                    # Mostrar por qué NO se detecta gesto cuando se intenta
                    if len(gestures_detected) == 0:
                        cv2.putText(frame, "Intenta: Puno inclinado o Pistola perfecta", (10, y_pos + 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 255), 1)
        
        else:
            cv2.putText(frame, "NO SE DETECTA MANO", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Instrucciones
        cv2.putText(frame, "Prueba diferentes gestos:", (10, h-60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, "Puno inclinado, Pistola, Paz, Palma, Cordon", (10, h-40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, "ESC: Salir", (10, h-20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow('Debug Gestos', frame)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    debug_gestures()
