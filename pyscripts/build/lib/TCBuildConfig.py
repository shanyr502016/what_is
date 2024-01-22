""" TCBuildConfig get command line inputs for Build the Teamcenter Modules """

import os
from corelib.Loggable import Loggable

class TCBuildConfig(Loggable):
    """ TCBuildConfig will supports to get handle the command line inputs"""

    def __init__(self, args): 
    
        super().__init__(__name__)

        self._arguments = args._arguments # initialization


    def get_workspace(self):
        """ Git Checkout Workspace location will get from command line """
        try:
            if 'workspace' in self._arguments:
                return getattr(self._arguments, 'workspace')
            else:                
                raise ValueError('--workspace is required')
        except ValueError as e:
            self.log.error(f"WorkSpace Error: {e}")
            return False
        
    def get_branch(self):   
        """ Git Branch names will get from command line""" 
        try:
            if 'branch' in self._arguments:
                return getattr(self._arguments, 'branch')
            else:                
                raise ValueError('--branch is required')
        except ValueError as e:
            self.log.error(f"Branch Error: {e}")
            return False
        
    def get_software_version(self):
        """ Get Software version will get from command line"""
        try:
            if 'software_version' in self._arguments:
                return getattr(self._arguments, 'software_version')
            else:                
                raise ValueError('--software_version is required')
        except ValueError as e:
            self.log.error(f"Software Version Error: {e}")
            return False        

    def get_package_name(self):
        """ Package Name will get from command line """
        try:
            if 'package_name' in self._arguments:
                return getattr(self._arguments, 'package_name')                
            else:                
                raise ValueError('--package_name is required')
        except ValueError as e:
            self.log.error(f"Package Name Error: {e}")
            return False

    def get_tc_version(self):
        """ TC Version will get from command line """
        try:
            if 'tc_version' in self._arguments:
                return getattr(self._arguments, 'tc_version')
            else:                
                raise ValueError('--tc_version is required')
        except ValueError as e:
            self.log.error(f"TC Version Error: {e}")
            return False        

    
    def get_artifacts_creation(self):
        """ Artifacts will get from command line to create the packages """
        try:
            if 'artifacts_creation' in self._arguments:
                return getattr(self._arguments, 'artifacts_creation')       
            else:                
                raise ValueError('--artifacts_creation is required')
        except ValueError as e:
            self.log.error(f"Artifacts Error: {e}")
            return False  

    def get_delta_build(self):
        """ Artifacts will get from command line to create the packages """
        try:
            if 'delta_build' in self._arguments:
                return getattr(self._arguments, 'delta_build')       
            else:                
                raise ValueError('--delta_build is required')
        except ValueError as e:
            self.log.error(f"Delta Build Error: {e}")
            return False     
        

    def get_bmide_out_folder_name(self, pattern, folder_name, software_version, bmide_build_version, tc_version ):

        """ BMIDE Output Folder Name"""
        try:
            if pattern:
                _pkg_name = pattern.replace('$FOLDER_NAME', str(folder_name))
                _pkg_name = _pkg_name.replace('$SOFTWARE_VERSION', str(software_version))
                _pkg_name = _pkg_name.replace('$BMIDE_BUILD_VERSION', str(bmide_build_version))
                _pkg_name = _pkg_name.replace('$TC_VERSION', str(tc_version)) 
                return _pkg_name      
            else:                
                raise ValueError('BMIDE Build Folder Name Error')
        except ValueError as e:
            self.log.error(f"BMIDE OUT Pattern Error: {e}")
            return False 