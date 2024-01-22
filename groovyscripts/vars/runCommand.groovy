


import com.lib.Utilities


def call(config) {

    // Execute the command based on the platform

    def utils = new Utilities() 
    def command = config.command    

    script {
        echo "[DEBUG INFO] Execution Command: ${command}"
        if (utils.findJobType(currentBuild) == 'Dev') {
            
            if (isUnix()) {
                echo "[DEBUG INFO] Platform: LNX"
                sh """ 
                    $command 
                """
            } else {
                echo "[DEBUG INFO] Platform: WIN"
                bat """ 
                    $command 
                """
            }
            echo "[DEBUG INFO] Detected jobType: ${utils.findJobType(currentBuild)}"
        } else {
            if (isUnix()) {
                echo "[DEBUG INFO] Platform: LNX"
                try {
                    sh """ 
                    $command 
                    """
                } catch (Exception e) {
                    echo "Error occurred: ${e.message}"
                }
            } else {
                echo "[DEBUG INFO] Platform: WIN"
                try {
                    bat """ 
                        $command 
                    """
                } catch (Exception e) {
                    echo "Error occurred: ${e.message}"
                }
            }
            
        }
        
    }

}
