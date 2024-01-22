
import groovy.json.JsonSlurperClassic

def call() {
    def jsonContent = readFileFromResources('global.json')
    return jsonContent
}


def readFileFromResources(String fileName) {

    def request = libraryResource fileName
    return new groovy.json.JsonSlurperClassic().parseText(request)
}
