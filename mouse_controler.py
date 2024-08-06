import pyautogui
from hand_movement_detector import detect_hand_movement
from threading import Thread, Lock
import time

# Configurações iniciais do mouse
screen_width, screen_height = pyautogui.size()
mouse_speed = 15  # Ajuste a velocidade do movimento do mouse

speed = 0 

# Variáveis globais para controle do movimento do mouse
movement_direction = "No significant movement"
direction_lock = Lock()

def move_mouse():
    global movement_direction
    global speed 
    while True:
        
        x, y = pyautogui.position()
        with direction_lock:
            current_direction = movement_direction
        
        if current_direction != "No significant movement":
            if current_direction == "Up":
                y -= mouse_speed * speed
            elif current_direction == "Down":
                y += mouse_speed * speed
            elif current_direction == "Left":
                x -= mouse_speed * speed
            elif current_direction == "Right":
                x += mouse_speed * speed

            # Garantir que o cursor permaneça dentro dos limites da tela
            x = max(0, min(screen_width - 1, x))
            y = max(0, min(screen_height - 1, y))

            pyautogui.moveTo(x, y, duration=0.2)
            print(f"Movendo {current_direction} - Pos Atual: {x} {y} - sd {speed} - d {mouse_speed * speed}", end='\r')
        else:
            time.sleep(0.2)  # Pequena pausa para evitar uso excessivo da CPU

def update_movement_direction():
    global movement_direction
    global speed
    try:
        for direction in detect_hand_movement():
            with direction_lock:
                movement_direction = direction['direction']
                speed = direction['speed']
    except KeyboardInterrupt:
        print("Detecção de movimento interrompida. Saindo...")
    finally:
        print("Finalizando a detecção de movimento.")

if __name__ == "__main__":
    try:
        # Iniciar a thread para controlar o movimento do mouse
        mouse_thread = Thread(target=move_mouse, daemon=True)
        mouse_thread.start()
        
        # Atualizar a direção do movimento com base na detecção das mãos
        update_movement_direction()
    except KeyboardInterrupt:
        print("Controle do mouse interrompido. Saindo...")
    finally:
        pass
        #pyautogui.moveTo(screen_width // 2, screen_height // 2)  # Opcional: Mover o cursor para o centro da tela
