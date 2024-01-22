

def call(config) {

    // PostBMIDE with Delta Executions
    
    String DITA_DEPLOY_SCRIPTS = config.DITA_DEPLOY_SCRIPTS
    String DITA_MANAGE_SCRIPTS = config.DITA_MANAGE_SCRIPTS
    String PACKAGE_LIST_TO_DEPLOY =  config.PACKAGE_LIST_TO_DEPLOY
    def parametersConfig =  config.parametersConfig
    def SUB_TARGETS_DEPLOYMENT_OPTIONS = config.SUB_TARGETS_DEPLOYMENT_OPTIONS

    if (PACKAGE_LIST_TO_DEPLOY != null) {
        echo "[DEBUG INFO] SUB_TARGETS_DEPLOYMENT_OPTIONS: ${SUB_TARGETS_DEPLOYMENT_OPTIONS}"
        String FSCStart_CMD = "${DITA_MANAGE_SCRIPTS} -m FSC -a Start -d"       
        String PostBMIDE_CMD = "${DITA_DEPLOY_SCRIPTS} -m PostBMIDE -p ${PACKAGE_LIST_TO_DEPLOY}"   
        PostBMIDE_CMD += delta([
            SUB_TARGETS_DEPLOYMENT_OPTIONS: SUB_TARGETS_DEPLOYMENT_OPTIONS,
            parametersConfig: parametersConfig,
            targetName: 'Deploy_PostBMIDE',
            DITA_CMD: PostBMIDE_CMD
        ])    
        if (params.START_DEPLOY_FROM_BEGINNING.equals(false)) {
            echo '[DEBUG INFO] PostBMIDE - Resume State Enabled'
            PostBMIDE_CMD += " -d"
        } else {
            echo '[DEBUG INFO] PostBMIDE - Resume State Disabled'
            PostBMIDE_CMD += " -d -r"
        }
        runCommand([command: FSCStart_CMD]) 
        runCommand([command: PostBMIDE_CMD])        
        checkErrorStatus([parametersConfig: parametersConfig,stagename: "Deploy_PostBMIDE"])
    }
}