
def call(config) {

    String GIT_PROJECT = config.GIT_PROJECT
    String GIT_REPOURL = config.GIT_REPOURL
    String GIT_BRANCH_NAME = config.GIT_BRANCH_NAME
    String GIT_BRANCH = config.GIT_BRANCH
    String credentialsId = config.credentialsId

    SOURCE_BASE_LOCATION_TEMP = '/data/jenkins-workspace/' + GIT_PROJECT + '/' + GIT_BRANCH   

    echo "[DEBUG INFO] [ ========[ Checkout Teamcenter Project from code.siemens.com Gitlog ]======== ]"

    try {

        dir(SOURCE_BASE_LOCATION_TEMP) {
            deleteDir()
        }

        dir(SOURCE_BASE_LOCATION_TEMP) {

            def data = checkout([$class: 'GitSCM', branches: [[name: '*/' + GIT_BRANCH_NAME]], 
                    extensions: [
                        // [$class: 'GitLFSPull']
                        ],
                    userRemoteConfigs: [
                        [credentialsId: credentialsId, 
                        url: GIT_REPOURL ]]])

            echo "[DEBUG INFO] GIT_COMMIT_INFO : ${data}"

            String GIT_COMMIT = data['GIT_COMMIT']

            def publisher = LastChanges.getLastChangesPublisher "PREVIOUS_REVISION", "SIDE", "LINE", true, true, "", "", "", "", ""
            publisher.publishLastChanges()
            def changes = publisher.getLastChanges()
            def diff = changes.getDiff()
                    
            println(changes.getCurrentRevision())

            // def commit_filelist = sh(script: "cd $SOURCE_BASE_LOCATION_TEMP && git ls-tree --name-only -r $GIT_COMMIT", returnStatus: true)

            // def fileList = commit_filelist.tokenize('\n')
            
            // print(commit_filelist)

            // fileList.each { fileName ->
            //     print("File: $fileName")
            // }

            // for file in $files
            // do
            //     author=$(git log --format="%an" -- $file | head -n 1)
            //     echo "File: $file | Author: $author"
            // done

            return commit_filelist

        }

    } catch (Exception e) {
        echo "[DEBUG INFO] [ ========[ Checkout Teamcenter Project from code.siemens.com Gitlog Failed ]======== ]"
        return null
    }
    

   
}