/**
 * This script can be run via the Jenkins CLI as follows:
 *
 * java -jar /var/jenkins/war/WEB-INF/jenkins-cli.jar -s http://localhost:8080 groovy addCredentials.groovy
 *
 * For a given json file, this script will create a set of credentials.
 * The script can be run safely multiple times and it will update each changed credential
 * (deleting credentials is not currently supported).
 *
 * This is useful in conjunction with the job-dsl to bootstrap a barebone Jenkins instance.
 *
 * This script will currently fail if the plugins it requires have not been installed:
 *
 * credentials-plugin
 * credentials-ssh-plugin
 */


import com.cloudbees.plugins.credentials.Credentials
import com.cloudbees.plugins.credentials.CredentialsScope
import com.cloudbees.plugins.credentials.common.IdCredentials
import com.cloudbees.plugins.credentials.domains.Domain
import hudson.model.*
import com.cloudbees.plugins.credentials.SystemCredentialsProvider
import com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl
import com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey
import groovy.json.JsonSlurper;

boolean addUsernamePassword(scope, id, username, password, description) {
    provider = SystemCredentialsProvider.getInstance()
    provider.getCredentials().add(new UsernamePasswordCredentialsImpl(scope, id, description, username, password))
    provider.save()
    return true
}

boolean addSSHUserPrivateKey(scope, id, username, privateKey, passphrase, description) {
    provider = SystemCredentialsProvider.getInstance()
    source = new BasicSSHUserPrivateKey.DirectEntryPrivateKeySource(privateKey)
    provider.getCredentials().add(new BasicSSHUserPrivateKey(scope, id, username, source, passphrase, description))
    provider.save()
    return true
}

boolean addSSHUserPrivateKeyFile(scope, id, username, privateKey, passphrase, description) {
    provider = SystemCredentialsProvider.getInstance()
    source = new BasicSSHUserPrivateKey.FileOnMasterPrivateKeySource(privateKey)
    provider.getCredentials().add(new BasicSSHUserPrivateKey(scope, id, username, source, passphrase, description))
    provider.save()
    return true
}

def jsonFile = new File("{{ jenkins_credentials_file_dest }}");

if (!jsonFile.exists()){
    throw RuntimeException("Credentials file does not exist on remote host");
}

def jsonSlurper = new JsonSlurper()
def credentialList = jsonSlurper.parse(new FileReader(jsonFile))

credentialList.each { credential ->

    if (credential.scope != "GLOBAL"){
        throw new RuntimeException("Sorry for now only global scope is supported");
    }

    scope = CredentialsScope.valueOf(credential.scope)

    def provider = SystemCredentialsProvider.getInstance();

    def toRemove = [];

    for (Credentials current_credentials: provider.getCredentials()){
        if (current_credentials instanceof IdCredentials){
            if (current_credentials.getId() == credential.id){
                toRemove.add(current_credentials);
            }
        }
    }

    toRemove.each {curr ->provider.getCredentials().remove(curr)};

    if (credential.type == "username-password") {
        addUsernamePassword(scope, credential.id, credential.username, credential.password, credential.description)
    }

    if (credential.type == "ssh-private-key") {

        if (credential.passphrase != null && credential.passphrase.trim().length() == 0){
            credential.passphrase = null;
        }

        addSSHUserPrivateKey(scope, credential.id, credential.username, credential.privatekey, credential.passphrase, credential.description)
    }

    if (credential.type == "ssh-private-keyfile") {

        if (credential.passphrase != null && credential.passphrase.trim().length() == 0){
            credential.passphrase = null;
        }

        addSSHUserPrivateKeyFile(scope, credential.id, credential.username, credential.privatekey, credential.passphrase, credential.description)
    }
}
