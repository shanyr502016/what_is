from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.File import Directory, File
import os

class UtilityExecutionSet(Loggable):
    
    def __init__(self, environment_provider, commands, configFilename, parallel): 
        
        super().__init__(__name__)

        self._environment_provider = environment_provider

        self._commands = commands

        self._configFilename = configFilename

        self._parallel = parallel

    def execute(self):

        commands = []

        _utility_file = self._environment_provider.get_dita_log_path()
        
        if not os.path.exists(_utility_file):
            os.makedirs(_utility_file)

        config_file = File(_utility_file, self._configFilename + '.txt')
        for command in self._commands:
            commands.append(command)
        config_file.write_lines(commands)
        args = ['utility_execution_set', '-loginType=AUTO', '-configFile=' + config_file.path]
        args = ' '.join([str(elem) for elem in args])        
        process = Process(args)
        process.set_parallel_execution(self._parallel)
        result = process.execute()
        return result

