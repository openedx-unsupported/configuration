The edX *datajam stack* is a Vagrant instance designed for local development for datajam participants.  The instance:

* Uses the same system dependencies as edX production.
* Simplifies certain production settings to make development more convenient.  For example, it disables **nginx** and **gunicorn** in favor of **runserver** for Django development.

The datajam instance is designed to run code and tests, but you can do most development in the host environment:

* Git repositories are shared with the host system, so you can use your preferred text editor/IDE.
* You can load pages served by the running Vagrant instance.

The datajam configuration has the following components:
* LMS (student facing website)
* Studio (course authoring)
* Forums / elasticsearch / ruby (discussion forums)
* Insights (streaming analytics)

# Installing the edX Datajam Stack

* Install [Virtualbox >= 4.2.18](https://www.virtualbox.org/wiki/Download_Old_Builds_4_2)
* Install [Vagrant >= 1.3.4](https://github.com/edx/configuration/wiki/Installing-Vagrant)
* Install the `vagrant-hostsupdater` plugin:

    vagrant plugin install vagrant-hostsupdater

* Install [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/en/latest/install.html)
* Install [git](http://git-scm.com/book/en/Getting-Started-Installing-Git)
* Create a directory to store the image

    mkdir /opt/edx-datajam

    cd /opt/edx-datajam

* Download the installation script

    wget https://raw.github.com/edx/configuration/datajam/util/datajam

    chmod a+x datajam

* Run the installation script to setup the environment

    ./datajam create

* Once it completes, you should be able to log in to the virtual machine

    ./datajam ssh


# Using the edX Datajam Stack

It is recommended you open up a separate terminal for each application and and run them in the foreground so that you can monitor them closely.

## LMS Workflow

* Within the Vagrant instance, switch to the edxapp account:

    sudo su edxapp

*This will source the edxapp environment (`/edx/app/edxapp/edxapp_env`) so that the venv python, rbenv ruby and rake are in your search path.  It will also set the current working directory to the edx-platform repository (`/edx/app/edxapp/edx-platform`).*

* Start the server

    edx-lms-devserver

* Open a browser on your host machine and navigate to ``localhost:8000`` to load the LMS.  (Vagrant will forward port 8000 to the LMS server running in the VM.)

## Studio Workflow

* Within the Vagrant instance, switch to the edxapp account:

    sudo su edxapp

*This will source the edxapp environment (`/edx/app/edxapp/edxapp_env`) so that the venv python, rbenv ruby and rake are in your search path.  It will also set the current working directory to the edx-platform repository (`/edx/app/edxapp/edx-platform`).*

* Start the server

    edx-cms-devserver

* Open a browser on your host machine and navigate to ``localhost:8001`` to load Studio.  (Vagrant will forward port 8001 to the Studio server running in the VM.)


## Insights Workflow

* Within the Vagrant instance, switch to the edxapp account:

    sudo su edxapp

*This will source the edxapp environment (`/edx/app/edxapp/edxapp_env`) so that the venv python, rbenv ruby and rake are in your search path.  It will also set the current working directory to the edx-platform repository (`/edx/app/edxapp/edx-platform`).*

* Start the server

    edx-insights-devserver


## Forum Workflow

* Within the Vagrant instance, switch to the forum account

    sudo su forum

* Start the server

    edx-forum-devserver

* Access the API at ``localhost:4567`` (Vagrant will forward port 4567 to the Forum server running in the VM.)

## Logging In

Login to the LMS and CMS with the user "datajam@edx.org" with password "datajam."

# Issues / Workarounds

* All Platforms
    * If you see an error message that looks something like

        /path/to/some/bin/python: No module named virtualenvwrapper
        virtualenvwrapper.sh: There was a problem running the initialization hooks. 

        If Python could not import the module virtualenvwrapper.hook_loader,
        check that virtualenv has been installed for
        VIRTUALENVWRAPPER_PYTHON=/path/to/some/bin/python and that PATH is
        set properly.
        /path/to/some/bin/python: No module named virtualenvwrapper
        virtualenvwrapper.sh: There was a problem running the initialization hooks.

      then another virtualenv was active when you started the `datajam` script.  Run `deactivate` and try again.
    * If you see an error message that looks like
        [default] Mounting NFS shared folders...
        The following SSH command responded with a non-zero exit status.
        Vagrant assumes that this means the command failed!

        mount -o 'vers=3,udp' 192.168.33.1:'/path/to/edx-platform' /edx/app/edxapp/edx-platform

        Stdout from the command:

        Stderr from the command:

        stdin: is not a tty
        mount.nfs: requested NFS version or transport protocol is not supported

      It is likely that `nfsd` is not running properly on your host machine or is being blocked by a firewall.  Ensure that it is running and accessible and then try again.

* Mac OS X
    * If you get an error such as `NS_ERROR_FAILURE`, try upgrading VirtualBox (4.3.2 seems to solve this on OS/X Mavericks).
* Ubuntu
    * If you are working on an Ubuntu workstation and your home directory is encrypted you will likely run into NFS problems. To work around the issue use a root directory that is not on an encrypted volume.
    * If you see this message:

        It appears your machine doesn't support NFS, or there is not an
        adapter to enable NFS on this machine for Vagrant. Please verify
        that `nfsd` is installed on your machine, and try again. If you're
        on Windows, NFS isn't supported. If the problem persists, please
        contact Vagrant support.

      you need to install nfs using this command:

        sudo apt-get install nfs-common nfs-kernel-server

    * If the script appears to hang at `[default] Mounting NFS shared folders...`, exit it using Ctrl-C and then
        * Modify /etc/exports to remove the vagrant related lines at the bottom
        * Run

            sudo service nfs-kernel-server restart
