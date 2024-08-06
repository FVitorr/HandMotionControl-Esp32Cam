import cv2
import numpy as np
import mediapipe as mp
from receive_video import receive_frame

# Configurar MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

pixel_min_y = 5  # Mínimo de pixels para considerar um movimento válido verticalmente
pixel_min_x = 8  # Mínimo de pixels para considerar um movimento válido horizontalmente
hand_open_threshold = 0.10  # Threshold para considerar a mão aberta
acceleration_factor = 0.5  # Fator de aceleração para o movimento
min_speed = 1 # Velocidade mínima do movimento
max_speed = 100  # Velocidade máxima do movimento

def is_hand_open(hand_landmarks):
    # Verifica a distância entre a ponta dos dedos e a palma da mão
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]
    pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]

    # Distância entre a ponta dos dedos e a base do dedo (palma)
    index_distance = np.sqrt((index_tip.x - hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP].x) ** 2 +
                             (index_tip.y - hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP].y) ** 2)
    middle_distance = np.sqrt((middle_tip.x - hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP].x) ** 2 +
                              (middle_tip.y - hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP].y) ** 2)
    ring_distance = np.sqrt((ring_tip.x - hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_MCP].x) ** 2 +
                            (ring_tip.y - hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_MCP].y) ** 2)
    pinky_distance = np.sqrt((pinky_tip.x - hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_MCP].x) ** 2 +
                             (pinky_tip.y - hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_MCP].y) ** 2)

    return (index_distance < hand_open_threshold and
            middle_distance < hand_open_threshold and
            ring_distance < hand_open_threshold and
            pinky_distance < hand_open_threshold)

def detect_hand_movement():
    previous_y = None
    previous_x = None
    last_movement_direction = "No significant movement"
    last_movement_distance = 0  # Distância percorrida na direção do movimento

    c_speed = {'movement_speed': 1, 'last_movement_direction' : last_movement_direction}

    for frame in receive_frame():
        frame_image = cv2.imdecode(np.frombuffer(frame, np.uint8), cv2.IMREAD_COLOR)
        frame_image = cv2.flip(frame_image, 1)  # Inverter horizontalmente se necessário

        
        # Determinar a direção do movimento
        movement_direction = last_movement_direction


        
        if frame_image is not None:
            # Converter o frame para RGB (MediaPipe usa RGB)
            rgb_frame = cv2.cvtColor(frame_image, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame_image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    # Obter a posição do centro da palma da mão
                    palm_y = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].y * frame_image.shape[0]
                    palm_x = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x * frame_image.shape[1]

                    # Verificar se a mão está aberta ou fechada
                    if is_hand_open(hand_landmarks):
                        movement_direction = "No significant movement"
                        last_movement_distance = 0  # Resetar a distância
                        c_speed['movement_speed'] = 0
                    else:
                        if previous_y is not None and previous_x is not None:
                            delta_y = palm_y - previous_y
                            delta_x = palm_x - previous_x


                            # Atualizar a direção do movimento
                            if abs(delta_y) > abs(delta_x):
                                if delta_y < -pixel_min_y:
                                    movement_direction = "Up"
                                elif delta_y > pixel_min_y:
                                    movement_direction = "Down"
                            else:
                                if delta_x < -pixel_min_x:
                                    movement_direction = "Left"
                                elif delta_x > pixel_min_x:
                                    movement_direction = "Right"

                            # Calcular a distância percorrida
                            distance = np.sqrt(delta_x**2 + delta_y**2)

                            # Aplicar aceleração se movendo na mesma direção
                            if (delta_y > pixel_min_y and movement_direction == "Down") or \
                               (delta_y < -pixel_min_y and movement_direction == "Up") or \
                               (delta_x > pixel_min_x and movement_direction == "Right") or \
                               (delta_x < -pixel_min_x and movement_direction == "Left"):
                                if c_speed['last_movement_direction'] == movement_direction:
                                    c_speed['movement_speed'] += (distance / last_movement_distance) * acceleration_factor
                                else:
                                    c_speed['last_movement_direction'] = movement_direction
                                    c_speed['movement_speed'] = 0
                            else:
                                #c_speed['movement_speed'] = 1
                                pass

                            # Limitar a velocidade do movimento a um intervalo
                            c_speed['movement_speed'] = max(min_speed, min(c_speed['movement_speed'], max_speed)) if movement_direction != "No significant movement" else 0

                            
                            last_movement_distance = distance

                    last_movement_direction = movement_direction

                    previous_y = palm_y
                    previous_x = palm_x

                    # Exibir a direção e a velocidade do movimento no frame
                    cv2.putText(frame_image, last_movement_direction, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    cv2.putText(frame_image, f"Speed: {c_speed['movement_speed']:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            else:
                movement_direction = "No significant movement"
                c_speed['movement_speed'] = 0
            # Exibir o frame com a detecção de movimento
            cv2.imshow('Hand Movement', frame_image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            return_ = {'direction': movement_direction, 'speed': c_speed['movement_speed']}
        
            yield return_

if __name__ == "__main__":
    try:
        detect_hand_movement()
    except KeyboardInterrupt:
        print("Detecção de movimento interrompida. Saindo...")
    finally:
        cv2.destroyAllWindows()