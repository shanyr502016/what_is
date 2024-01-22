from corelib.Loggable import Loggable
from corelib.Process import Process
import os
from corelib.File import BaseFile
from corelib.SCP import SCP

class BackupUtilities(Loggable):
    
    def __init__(self, environment_provider):  
        
        super().__init__(__name__)
        
        self.backup_filename = None
        self.backup_source = None
        self._environment_provider = environment_provider
        
        self.backup_args = []

    def set_backup_filename(self, backup_filename):   
             
        self.backup_filename = backup_filename
        
        
    def set_backup_source(self, backup_source, server_info, action_msg):
        
        self.backup_source = backup_source
        __ssh_command = self._environment_provider.get_ssh_command(server_info)
        
        if __ssh_command == '':
            if not os.path.exists(self.backup_source):
                self.log.warning(f"Source Directory is not exists {self.backup_source}. Skipped {action_msg}")
                return False
            return True
        else:

            _remote_path  = SCP(__ssh_command).check_dir_to_remote(self._environment_provider.is_windows(server_info['OS_TYPE']),backup_source)

            if _remote_path:
                return True
            else:
                self.log.warning(f"Source Directory is not exists {self.backup_source}. Skipped {action_msg}")
                return False

        
        
    def set_backup_dest(self, backup_dest, server_info):

        self.backup_dest = backup_dest
        __ssh_command = self._environment_provider.get_ssh_command(server_info)

        try:
            if __ssh_command == '': 
                if not os.path.exists(self.backup_dest):
                    os.makedirs(self.backup_dest)
            else:
                args = [__ssh_command]
                if self._environment_provider.is_windows(server_info['OS_TYPE']):
                    args.append('if not exist ' + self.backup_dest + ' mkdir ' + self.backup_dest)
                else:
                    args.append('mkdir -p '+ self.backup_dest)
                    args = ' '.join([str(elem) for elem in args]) 
                    process = Process(args)
                    process.hide_output()
                    process.collect_output()
                    process.ignore_errors()
                    process.execute()
        except (Exception) as err:
            self.log.error(err)

        
    def set_backup_env(self, server_info, excludes: list = None):
        
        __ssh_command = self._environment_provider.get_ssh_command(server_info) 
        try:
            if __ssh_command == '':
                self.backup_args = []
            else:
                self.backup_args = [__ssh_command]

            if self._environment_provider.is_linux(server_info['OS_TYPE']):
                self.backup_args.extend(['tar', '-pczf']) 
                self.backup_args.extend([os.path.join(self.backup_dest, self.backup_filename + '.tar.gz')]) 
                if excludes is not None:
                    for entry in excludes:
                        exclude_path = BaseFile.get_obj_path(entry)
                        self.backup_args.extend(["--exclude=" + exclude_path])
                self.backup_args.extend(['-C',self.backup_source, '.']) 
            if self._environment_provider.is_windows(server_info['OS_TYPE']):
                if '7ZIP_PATH' in server_info:
                    self.backup_args.extend([server_info['7ZIP_PATH'], 'a', '-t7z', '-m0=lzma2', '-mx=5', '-mfb=64', '-md=32m', '-ms=on'])
                    self.backup_args.extend([os.path.join(self.backup_dest, self.backup_filename + '.7z')])
                    self.backup_args.extend([self.backup_source]) 
                    if excludes is not None:
                        for entry in excludes:
                            exclude_path = BaseFile.get_obj_path(entry)
                            self.backup_args.extend(['-mx0 -xr!'+ exclude_path])
                    
                else:
                    self.log.info("Please set 7ZIP_PATH in Configuration file")  
        except (Exception) as err:
            self.log.error(err)
            

    def get_backup_command(self):       
        return ' '.join([str(elem) for elem in self.backup_args])
    
        

    