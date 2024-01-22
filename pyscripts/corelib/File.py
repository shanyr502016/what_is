
import os
import tempfile
import shutil

class BaseFile:
    def __init__(self, path, *name):
        """
        Represents a single file system item (file/folder).
        """

        path = BaseFile.get_obj_path(path)

        if name is None or len(name) == 0:
            self.path = path
        else:
            self.path = os.path.join(path, *name)
    @staticmethod
    def get_obj_path(obj):
        """
        Returns the path of the given object.
        The object can be a string or any subclass of BaseFile
        """
        if isinstance(obj, BaseFile):
            return obj.path
        return obj

class File(BaseFile):


    def __init__(self, path, *name):
        
        super().__init__(path, *name)

    def exists(self):
        """
        Checks if this file exists

        """
        return os.path.isfile(self.path)
    
    def read_content(self, encoding=None):
        """
        Reads the entire content of the file
        """
        with open(self.path, encoding=encoding) as f:
            return f.read()
        
    def write(self, content, append: bool = False):
        """
        Writes the given content to the file.
        Any existing content will be overwritten if not otherwise specified
        """

        with open(self.path, 'a' if append else 'w+') as f:
            f.write(content)
    
    def write_lines(self, lines, line_ending: str = '\n', append: bool = False):
        """
        Writes the given string list in a file. Each list entry in a single line.
        """
        with open(self.path, 'a' if append else 'w+') as f:
            for item in lines:
                f.write(item + line_ending)
                
                
    def find_replace_content(self, find_str, replace_str):
    
        try:
        
            file_content = self.read_content('utf-8')
        
            # Perform find and replace in the content
            updated_content = file_content.replace(find_str, replace_str)
        
            self.write(updated_content)
            return 0
        except Exception as e:
            print(f"File '{self.path}' does not exist.")
            return 1
            
            
    def remote_write_new_file(self, ssh_client, content):
        _result = 1
        try:
            sftp = ssh_client.sftp_connection(ssh_client.connect())
            # Write the content to the remote file
            with sftp.file(self.path, 'w') as remote_file:
                remote_file.write(content)
            _result = 0
        except FileNotFoundError:
            print(f"File '{self.path}' does not exist.")
            _result = 1
            return _result
        finally:
            sftp.close()
            return _result
        
                
    def remote_find_replace_content(self, ssh_client, find_str, replace_str):
        _result = 1
        try:
            sftp = ssh_client.sftp_connection(ssh_client.connect())
            sftp.stat(self.path)
            with sftp.file(self.path, 'r') as remote_file:
                file_content = remote_file.read().decode('utf-8')
                
            # Perform find and replace in the content
            updated_content = file_content.replace(find_str, replace_str)
            
            # Write the updated content back to the remote file
            with sftp.file(self.path, 'w') as remote_file:
                remote_file.write(updated_content.encode('utf-8'))
            _result = 0
        except FileNotFoundError:
            print(f"File '{self.path}' does not exist.")
            _result = 1
            return _result
        finally:
            sftp.close()
            return _result
            
        
class Directory():

    def __init__(self):

        super().__init__()


    def get_name(self):

        """
        Returns the name of the directory
        """
        return os.path.basename(self.path)


    def create(self, path):
        """
        Creates the current directory if its not exist
        """
        if self.exists(path):
            return True
        os.makedirs(path)
        return True

    def exists(self, path):
        """
        Checks if this directory exists
        """
        return os.path.exists(path)


    @classmethod
    def get_temp_dir(cls):
        """
        Returns the current temporary directory.
        """
        return tempfile.gettempdir()


    @classmethod
    def get_home_dir(cls):
        """
        Returns the home directory of the current user
        """
        return os.path.expanduser('~')
    

    def removedirs(self, dirpath):
        """
        Remove the directory and subdirectory
        """

        return shutil.rmtree(dirpath, ignore_errors=True)
        
    def is_empty(self, path):
        with os.scandir(path) as scanner:
            for entry in scanner: # this loop will have maximum 1 iteration
                return False # found file, not empty.
        return True # if we reached here, then empty.