/**
 * This script can be run via the Jenkins CLI as follows:
 *
 * java -jar /var/jenkins/war/WEB-INF/jenkins-cli.jar -s http://localhost:8080 groovy addCredentials.groovy
 *
 * For a given json file, it will create credential in a Jenkins instance.  The script can be run safely
 * multiple times and it will update a credential.
 *
 * This is useful in conjunction with the job-dsl to bootstrap an barebones Jenkins instance.
 *
 * This script will currently fail if the plugins it requires have not been installed:
 *
 * credentials-plugin
 * credentials-ssh-plugin
 *
 * TODO: Deleting credentials is not currently supported.
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
    println scope
    return true
}

boolean addSSHUserPrivateKey(scope, id, username, privateKey, passphrase, description) {
    provider = SystemCredentialsProvider.getInstance()
    source = new BasicSSHUserPrivateKey.DirectEntryPrivateKeySource(privateKey)
    provider.getCredentials().add(new BasicSSHUserPrivateKey(scope, id, username, source, passphrase, description))
    provider.save()
    println scope
    return true
}

def jsonSlurper = new JsonSlurper()
def d = jsonSlurper.parse(new FileReader(new File("{{ jenkins_credentials_file_dest }}")))

d.credentials.each { cred ->

    if (cred.scope != "GLOBAL"){
        throw new RuntimeException("Sorry for now only global scope is supported");
    }

    scope = CredentialsScope.valueOf(cred.scope)

    def provider = SystemCredentialsProvider.getInstance();

    def toRemove = [];

    for (Credentials current_credentials: provider.getCredentials()){
        if (current_credentials instanceof IdCredentials){
            if (current_credentials.getId() == cred.id){
                toRemove.add(current_credentials);
            }
        }
    }

    toRemove.each {curr ->provider.getCredentials().remove(curr)};

    if (cred.type == "username-password") {
        addUsernamePassword(scope, cred.id, cred.username, cred.password, cred.description)
    }

    if (cred.type == "ssh-private-key") {
        addSSHUserPrivateKey(scope, cred.id, cred.username, cred.privatekey, cred.passphrase, cred.description)
    }
}
