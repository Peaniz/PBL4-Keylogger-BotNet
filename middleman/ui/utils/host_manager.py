import json
import os

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
                return []
        return []

    def add_host(self, ip):
        if ip not in self.hosts:
            self.hosts.append(ip)
            self.save_hosts()

    def remove_host(self, ip):
        if ip in self.hosts:
            self.hosts.remove(ip)
            self.save_hosts()

    def get_hosts(self):
        return self.hosts

    def save_hosts(self):
        with open(self.filename, 'w') as f:
            json.dump(self.hosts, f) 