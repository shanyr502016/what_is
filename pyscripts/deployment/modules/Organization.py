"""
Organization deployment activities
"""
from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
import os
import shutil
from corelib.Constants import Constants



class Organization(Loggable):
    
    def __init__(self, args):   

        super().__init__(__name__)
        """
        Set arguments from DynamicImporter
        """         
        self.__arguments = args        
        """
        Get the Environment Specific Values from config json
        """        
        self.__environment = args._environment
        """
        Get the Module Specific Values from config json
        """        
        self.__properties = args._properties
        """
        Get the Environment Provider method
        Reusable method derived
        """        
        self.__environment_provider = args._environment_provider
        """
        Module name from user commandline (Only Module (classname))
        """       
        self.__module_name = args._module_name
        self.__module = args._arguments.module
        self.__module_label = self.__module
        """
        Sub Module name from user commandline (Only Sub Module (classname))
        """
        self.__sub_module_name = args._sub_module_name

        """
        Target Teamcenter Package ID get from user commandline
        """        
        self._tcpackage_id = args._tcpackage_id

        """
        Target Instances setup
        """        
        self.__target = None
        """
        Remote Execution.
        """
        self.__remote_execution = False 
        
        """
        Scope and target setup based on configuration
        """ 

        if self.__sub_module_name:
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name)


        self._processes = []
        self._processesResult = []
        self._parallel = self.__arguments.parallel
        
        self._input_file = args._input_file
        
    def default(self): 

        return self._executeTargets()  

    def frigg(self):

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])        

        for index, server_info in enumerate(_execute_servers):

            self.log.info(f"Organization Frigg")

            try:

                if self._input_file != '':
                    _inputFilepath = self._input_file
                else:
                    _inputFilepath = self.__properties[self.__target]['inputpath'] 

                mapping_configuration = self.__properties[self.__target]['mapping_configuration']

                self.log.info(f'Reading the Frigg input File from {_inputFilepath}')


                if os.path.isdir(_inputFilepath):
                    if os.path.exists(_inputFilepath):
                        _inputpath = _inputFilepath
                        _outputsuccesspath = os.path.join(_inputFilepath, 'success_files')
                        _outputfailurepath = os.path.join(_inputFilepath, 'failure_files')
                        path_list = os.listdir(_inputFilepath)


                elif os.path.isfile(_inputFilepath) and  _inputFilepath.endswith('.txt'):
                    _inputpath = '/'.join(_inputFilepath.split('/')[0:-1])
                    _outputsuccesspath = os.path.join(_inputpath, 'success_files')
                    _outputfailurepath = os.path.join(_inputpath, 'failure_files')
                    path_list = [_inputFilepath.split('/')[-1]]
                
                else:
                    path_list = None

                if path_list != None:
                    if not os.path.exists(_outputsuccesspath):
                        os.makedirs(_outputsuccesspath)

                    if not os.path.exists(_outputfailurepath):
                        os.makedirs(_outputfailurepath) 

                    for inputfile in path_list:                      
                        outputLines = []
                        if inputfile.endswith('.txt'):
                            _outputFile = 'success_'+ inputfile
                            with open(os.path.join(_inputpath,inputfile), 'r') as fin:
                                lines = fin.readlines()
                                for line in lines:
                                    for mapping_config in mapping_configuration.keys():
                                        line = line.replace(mapping_config,mapping_configuration[mapping_config])
                                    outputLines.append(line) 
                            with open(os.path.join(_outputsuccesspath, _outputFile), 'w') as fout:
                                fout.writelines(outputLines) 
                            self.log.info(f'Replacement the Mapping Configuration {_outputFile}') 
                            command  =' '.join([str(elem) for elem in self.__build_arguments(server_info)])+' '+'-file='+ os.path.join(_outputsuccesspath,_outputFile) 
                            self.log.info(f"Execution Command: {command}") 
                            result = self._execute(command, _outputsuccesspath)
                            
                            if result == 0:
                                shutil.move(os.path.join(_inputpath,inputfile), os.path.join(_outputsuccesspath, _outputFile))
                            else:
                                os.remove(os.path.join(_outputsuccesspath, _outputFile))
                                shutil.move(os.path.join(_inputpath,inputfile), os.path.join(_outputfailurepath, 'failure_' + inputfile))
                            self._processes.append({'NODE':server_info['NODE'],'process': result, 'module': self.__module_label, 'package_id': '', 'label': f"Make User - [{inputfile}]"})
                            if not self._parallel:
                                self.__console_msg(result, f"Make User - [{inputfile}]]")
                        else:
                            self.log.warning(f'{inputfile} - Skipped not supported Folder or File')

                else:
                    self.log.warning(f'{_inputFilepath} Not Exists.')

            except Exception as exp:
                self.log.error(exp)
                self._processes.append({'NODE':server_info['NODE'],'process': 1, 'module': self.__module_label, 'package_id': '', 'label': f"Make User"})
        return self._processes


    def makeuser(self):      
         
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])        

        for index, server_info in enumerate(_execute_servers):
            """
            Action: Make User
            Command:  make_user -u= -g= -pf= file=
            """              
            self.log.info(f"Organization Make User")

            for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):

                _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])
                try:
                    if os.path.exists(_location_in_package):
                        for file in sorted(os.listdir(_location_in_package)):
                            command  =' '.join([str(elem) for elem in self.__build_arguments(server_info)])+' '+'-file='+_location_in_package+'/'+file
                            self.log.info(f"Execution Command: {command}")
                            result = self._execute(command, _location_in_package)
                            self._processes.append({'NODE':server_info['NODE'],'process': result, 'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - Make User"})
                            if not self._parallel:
                                self.__console_msg(result, f"[{tc_package_id}] - Make User")       
                    else:
                        self.log.warning(f"Required File or Folder not Present from this location {tc_package_id}. {__class__.__name__} Skipped")
                except Exception as exp:
                    self.log.error(exp)
                    self._processes.append({'NODE':server_info['NODE'],'process': 1, 'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - Make User"})
        return self._processes

        
    def __build_arguments(self, _server_info):
        
        __ssh_command = self.__environment_provider.get_ssh_command(_server_info)
        
        if __ssh_command == '':
            self.__remote_execution = False  
        else:
            self.__remote_execution = True
    
        if self.__remote_execution:
            args = [__ssh_command,
                    self.__properties[self.__target]['command'],
                    '-u='+ _server_info['TC_USER'],
                    '-g='+ _server_info['TC_GROUP'],
                    '-pf='+ _server_info['TC_PWF'],  
                ]       
        else:
            args = [self.__properties[self.__target]['command'],
                    '-u='+ _server_info['TC_USER'],
                    '-g='+ _server_info['TC_GROUP'],
                    '-pf='+ _server_info['TC_PWF'],
                ]
            
            
        return args        
        
    def _executeTargets(self):
        try:
            for threadcount, targets in enumerate(self.__environment_provider.get_execute_targets(self.__module_name).split(',')): 
                # Execute with multiple targets
                if not self.__sub_module_name:   
                    self.__target = targets   
                    dynamicExecutor = DynamicExecutor(self.__arguments)   
                    dynamicExecutor.set_module_instance(targets) # module instance name
                    # calling the targets one by one
                    if dynamicExecutor.get_sub_module_name():
                        _processesResult = getattr(Organization, dynamicExecutor.get_sub_module_name())(self)   
                    else:
                        _processesResult = dynamicExecutor.run_module()  
                    self._processesResult = self._processesResult + _processesResult 
            return self._processesResult               
        except Exception as exp:
            self.log.error(exp)


    def _execute(self, command, path):
        """ 
        Used to process services/command
        """
        process = Process(command, path)
        process.set_parallel_execution(self._parallel)
        return process.execute()
    
    
    def __console_msg(self, result, action_msg):
        if result == 0:
            self.log.info(Constants.colorize(f"{action_msg} Created Successfully!.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg} Failed.")
        self.log.info('..............................................................')
