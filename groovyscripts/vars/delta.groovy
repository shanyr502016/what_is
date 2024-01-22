
import com.lib.Utilities


def call(config) {

    def utils = new Utilities() 

    def SUB_TARGETS_DEPLOYMENT_OPTIONS = config.SUB_TARGETS_DEPLOYMENT_OPTIONS
    def parametersConfig = config.parametersConfig
    def targetName = config.targetName
    def DITA_CMD = config.DITA_CMD

    def totalTargets = utils.getMapValuesFromKey(parametersConfig['deploymentsubConfig']['deploymentsubtargets'], targetName).size()

    def deltatargets = SUB_TARGETS_DEPLOYMENT_OPTIONS[targetName].join(',')   
    
    return deltaPackage(SUB_TARGETS_DEPLOYMENT_OPTIONS, totalTargets, targetName, deltatargets)

}


def deltaPackage(SUB_TARGETS_DEPLOYMENT_OPTIONS, totalTargets, targetName, deltatargets) {
    def delta_cmd = ""
    if ((SUB_TARGETS_DEPLOYMENT_OPTIONS[targetName].size() != 0)) {

        if (SUB_TARGETS_DEPLOYMENT_OPTIONS[targetName].size() == totalTargets) {
            echo "[DEBUG INFO] ${targetName} With Full"
            delta_cmd = ""

        } else {
            echo "[DEBUG INFO] ${targetName} With Delta"
            delta_cmd = " -delta=${deltatargets}"

        }
    }
    return delta_cmd
}