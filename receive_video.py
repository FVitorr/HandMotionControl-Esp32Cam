import socket
import cv2
import numpy as np

# Configurações
UDP_IP = "0.0.0.0"  # Escutar em todas as interfaces de rede disponíveis
UDP_PORT = 8000
BUFFER_SIZE = 65536  # Tamanho máximo do buffer para recebimento de pacotes

# Criação do socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

def receive_frame():
    buffer = bytearray()

    while True:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        if data:
            buffer.extend(data)
            
            end_of_frame = buffer.find(b'\xFF\xD9')  # Final de uma imagem JPEG
            if end_of_frame != -1:
                frame_data = buffer[:end_of_frame + 2]
                buffer = buffer[end_of_frame + 2:]
                yield frame_data

if __name__ == "__main__":
    try:
        for frame in receive_frame():
            # Exibir o frame para debug
            frame_image = cv2.imdecode(np.frombuffer(frame, np.uint8), cv2.IMREAD_COLOR)
            if frame_image is not None:
                cv2.imshow('Video Stream', frame_image)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    except KeyboardInterrupt:
        print("Servidor interrompido. Saindo...")
    finally:
        sock.close()
        cv2.destroyAllWindows()
