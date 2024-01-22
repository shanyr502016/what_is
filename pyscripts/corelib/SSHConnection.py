"""
Using SSH Client 

"""

import paramiko
from corelib.Loggable import Loggable
import os
import xml.etree.ElementTree as ET

class SSHConnection(Loggable):

    def __init__(self, username, hostname, password=None):
    
        super().__init__(__name__)
        
        self.hostname = hostname
        self.username = username
        self.password = password
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Use the existing SSH agent
        self.client.load_system_host_keys()
        self.sftp = None        
        
    def connect(self):
    
        try:
            
            if self.password:
                self.client.connect(hostname=self.hostname, username=self.username,password=self.password)
            else:
                # Assuming SSH key authentication
                self.client.connect(hostname=self.hostname,username=self.username)
            return self.client    
        except paramiko.AuthenticationException:
            self.log.error("Authentication failed. Please check your credentials")
            return 1
        except paramiko.SSHException as e:
            self.log.error(f"SSH connection failed: {e}")
            return 1
            
            
    def sftp_connection(self, clients):        
        self.sftp = clients.open_sftp()        
        return self.sftp
        
            
    def close(self):
        if self.sftp:
            self.sftp.close()
        self.client.close()
        #self.log.debug(f"Remote Connection to {self.hostname} closed")
