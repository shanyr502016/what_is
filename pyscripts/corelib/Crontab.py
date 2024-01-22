import re
from corelib.Loggable import Loggable
from corelib.Process import Process
import os
from corelib.File import BaseFile, File, Directory
from corelib.SCP import SCP
from corelib.DateTime import DateTime
import tempfile



class Crontab(Loggable):


    def __init__(self):  
        
        super().__init__(__name__)
        
        self.__action = ''

        self.__is_windows= False

    def setAction(self, action):    
        self.__action = action

    def setSSHCommand(self, ssh_command):
        self.__ssh_command = ssh_command

    def setSCPWithOutSSH(self, scp_command):
        self.__scp_command = scp_command
    
    def setSCPWithSSH(self, scp_command):
        self.__scp_with_ssh = scp_command

    def get_content(self):

        content = self.__get_content(self.__ssh_command)

        location = self.__get_original_location(content)

        if location is not None and self.__scp_with_ssh.check_dir_to_remote(self.__is_windows, location):
            content=self.__scp_with_ssh.read_file_from_remote(location,self.__is_windows)
            return content
        return content


    @staticmethod
    def __get_content(ssh_command):

        args = [ssh_command]
        args.append('crontab -l')
        args = ' '.join([elem for elem in args])
        process = Process(args)
        process.hide_output()
        process.set_parallel_execution(True)
        process.collect_output()
        try:
            process.execute()
        except Exception:
            return ''
        return process.get_out_lines()


    @staticmethod
    def __get_status(contents):
        result = None
        for content in contents:            
            match = re.search(r'# Crontab (.+) by Dita', content)
            if match is not None:
                result = match.group(1)
                break            
        return result

    @staticmethod
    def __get_original_location(contents):
        result = None
        for content in contents:
            match = re.search(r'# Listing of Jobs in (.+)', content)
            if match is not None:
                result = match.group(1)
                break               
        return result


    @staticmethod
    def __get_crontab_file():
        """
        Returns the file which holds the content of the crontab when beeing stopped
        :return: File
        :rtype: File
        """
        return File(Directory.get_home_dir(), 'bin', 'crontab.mgr')    

    def update_content(self, new_content: str, force=False):
        self.log.debug(f'Updating crontab {new_content}')
        path = None
        if self.__ssh_command == '':
            tmp_file = File(Directory.get_temp_dir(), 'crontab_new')
            tmp_file.write(new_content)
            path = tmp_file.path
        else:
            tmp_file  = tempfile.NamedTemporaryFile('w+t')
            tmp_file_path = tmp_file.name
            tmp_file.write(new_content)
            tmp_file.flush()
            path = File(Directory.get_temp_dir(), 'crontab_new').path
            if self.__scp_command:
                self.__scp_command.copy_to_remote(tmp_file_path,File(Directory.get_temp_dir(), 'crontab_new'))
        args = [self.__ssh_command]
        args.append('crontab')
        args.append(path)
        args = ' '.join([elem for elem in args])
        process = Process(args)
        process.hide_output()
        return process.execute()

    def start(self):
        old_file = None
        content = self.__get_content(self.__ssh_command)
        location = self.__get_original_location(content)        
        if location is None:
            self.log.debug('Nothing to start: Crontab file not found')
            old_file = self.__get_crontab_file()
        else:
            old_file = File(location)
        if not self.__scp_with_ssh.check_dir_to_remote(self.__is_windows,old_file.path):
            self.log.error('File mentioned in crontab not found: ' + old_file.path)
            return
        old_content=self.__scp_with_ssh.read_file_from_remote(old_file.path,self.__is_windows)
        if self.update_content(old_content, force=True) == 0:
            return self.status()
        else:
            self.log.error("Crontab Start Failed")
            return self.status()


    def stop(self):

        content = self.__get_content(self.__ssh_command)
        location = self.__get_original_location(content)
        new_crontab = self.__get_crontab_file()
        replace_content = '# Crontab disabled by Dita - ' + DateTime.get_filename_timestamp() + '\n' + \
                          '# Listing of Jobs in ' + new_crontab.path + '\n'

        if self.update_content(replace_content) == 0:
            return self.status()
        else:
            self.log.error("Crontab Stop Failed")
            return self.status()

    def status(self):
        contents = self.__get_content(self.__ssh_command)
        if self.__action == 'status':
            for content in contents:
                self.log.debug(content)
        status = self.__get_status(contents)
        if status == 'Disabled':
            return '-'
        elif status == 'Enabled':
            return 'Running'