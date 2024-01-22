

def call(config) {

    // PreBMIDE with Delta Executions
    
    String DITA_DEPLOY_SCRIPTS = config.DITA_DEPLOY_SCRIPTS
    String DITA_MANAGE_SCRIPTS = config.DITA_MANAGE_SCRIPTS
    String PACKAGE_LIST_TO_DEPLOY =  config.PACKAGE_LIST_TO_DEPLOY
    def parametersConfig =  config.parametersConfig
    def SUB_TARGETS_DEPLOYMENT_OPTIONS = config.SUB_TARGETS_DEPLOYMENT_OPTIONS

    if (PACKAGE_LIST_TO_DEPLOY != null) {
        echo "[DEBUG INFO] SUB_TARGETS_DEPLOYMENT_OPTIONS: ${SUB_TARGETS_DEPLOYMENT_OPTIONS}"
        String PreBMIDE_CMD = "${DITA_DEPLOY_SCRIPTS} -m PreBMIDE -p ${PACKAGE_LIST_TO_DEPLOY}" 
        String FSCStart_CMD = "${DITA_MANAGE_SCRIPTS} -m FSC -a Start -d"

        PreBMIDE_CMD += delta([
                SUB_TARGETS_DEPLOYMENT_OPTIONS: SUB_TARGETS_DEPLOYMENT_OPTIONS,
                parametersConfig: parametersConfig,
                targetName: 'Deploy_PreBMIDE',
                DITA_CMD: PreBMIDE_CMD
            ])

        if (params.START_DEPLOY_FROM_BEGINNING.equals(false)) {
            echo '[DEBUG INFO] PreBMIDE - Resume State Enabled'
            PreBMIDE_CMD += " -d"
        } else {
            echo '[DEBUG INFO] PreBMIDE - Resume State Disabled'
            PreBMIDE_CMD += " -d -r"
        }
        runCommand([command: FSCStart_CMD]) 
        runCommand([command: PreBMIDE_CMD]) 
        checkErrorStatus([parametersConfig: parametersConfig,stagename: "Deploy_PreBMIDE"])  
    }

}