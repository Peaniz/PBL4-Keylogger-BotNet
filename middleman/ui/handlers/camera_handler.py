import pygame
import socket
import cv2
import numpy as np
import threading
import struct

def camreceiver(host, port=5002):
    global camera_running
    camera_running = True
    screen = pygame.display.get_surface()
    camera_panel_rect = pygame.Rect(100, 70, 600, 300)
    
    s = socket.socket()
    try:
        s.connect((host, port))
        s.settimeout(5.0)
        dat = b''
        payload_size = struct.calcsize("B")

        while camera_running:
            try:
                while len(dat) < payload_size:
                    packet = s.recv(4096)
                    if not packet:
                        raise ConnectionError("Connection closed by remote host")
                    dat += packet

                packed_count = dat[:payload_size]
                dat = dat[payload_size:]
                count = struct.unpack("B", packed_count)[0]

                frame_data = b''
                while count > 0:
                    if dat:
                        frame_data += dat
                        dat = b''
                    else:
                        packet = s.recv(4096)
                        if not packet:
                            raise ConnectionError("Connection closed by remote host")
                        frame_data += packet
                    count -= 1

                try:
                    img_array = np.frombuffer(frame_data, dtype=np.uint8)
                    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                    if img is not None:
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        img = cv2.resize(img, (600, 300))
                        img_surface = pygame.surfarray.make_surface(img)
                        
                        screen.blit(img_surface, camera_panel_rect.topleft)
                        pygame.display.update([camera_panel_rect])
                        pygame.time.delay(30)
                        
                        frame_data = b''
                        dat = b''
                except Exception as e:
                    print(f"Error processing frame: {e}")
                    continue

            except socket.timeout:
                print("Camera stream timeout")
                break
            except ConnectionError as e:
                print(f"Connection error: {e}")
                break
            except Exception as e:
                print(f"Error receiving camera data: {e}")
                break

    except Exception as e:
        print(f"Camera connection error: {e}")
    finally:
        camera_running = False
        try:
            s.close()
        except:
            pass
        
    return False