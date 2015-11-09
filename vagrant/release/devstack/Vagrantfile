Vagrant.require_version ">= 1.6.5"
unless Vagrant.has_plugin?("vagrant-vbguest")
  raise "Please install the vagrant-vbguest plugin by running `vagrant plugin install vagrant-vbguest`"
end

VAGRANTFILE_API_VERSION = "2"

MEMORY = 4096
CPU_COUNT = 2

$script = <<SCRIPT
if [ ! -d /edx/app/edx_ansible ]; then
    echo "Error: Base box is missing provisioning scripts." 1>&2
    exit 1
fi
OPENEDX_RELEASE=$1
export PYTHONUNBUFFERED=1
source /edx/app/edx_ansible/venvs/edx_ansible/bin/activate
cd /edx/app/edx_ansible/edx_ansible/playbooks

# Did we specify an openedx release?
if [ -n "$OPENEDX_RELEASE" ]; then
  EXTRA_VARS="-e edx_platform_version=$OPENEDX_RELEASE \
    -e certs_version=$OPENEDX_RELEASE \
    -e forum_version=$OPENEDX_RELEASE \
    -e xqueue_version=$OPENEDX_RELEASE \
  "
  CONFIG_VER=$OPENEDX_RELEASE
  # Need to ensure that the configuration repo is updated
  # The vagrant-devstack.yml playbook will also do this, but only
  # after loading the playbooks into memory.  If these are out of date,
  # this can cause problems (e.g. looking for templates that no longer exist).
  /edx/bin/update configuration $CONFIG_VER
else
  CONFIG_VER="master"
fi

ansible-playbook -i localhost, -c local run_role.yml -e role=edx_ansible -e configuration_version=$CONFIG_VER $EXTRA_VARS
ansible-playbook -i localhost, -c local vagrant-devstack.yml -e configuration_version=$CONFIG_VER $EXTRA_VARS

SCRIPT

MOUNT_DIRS = {
  :edx_platform => {:repo => "edx-platform", :local => "/edx/app/edxapp/edx-platform", :owner => "edxapp"},
  :themes => {:repo => "themes", :local => "/edx/app/edxapp/themes", :owner => "edxapp"},
  :forum => {:repo => "cs_comments_service", :local => "/edx/app/forum/cs_comments_service", :owner => "forum"},
  :ecommerce => {:repo => "ecommerce", :local => "/edx/app/ecommerce/ecommerce", :owner => "ecommerce"},
  :ecommerce_worker => {:repo => "ecommerce-worker", :local => "/edx/app/ecommerce_worker/ecommerce_worker", :owner => "ecommerce_worker"},
  :programs => {:repo => "programs", :local => "/edx/app/programs/programs", :owner => "programs"},
  :insights => {:repo => "insights", :local => "/edx/app/insights/edx_analytics_dashboard", :owner => "insights"},
  :analytics_api => {:repo => "analytics_api", :local => "/edx/app/analytics_api/analytics_api", :owner => "analytics_api"},
  # This src directory won't have useful permissions. You can set them from the
  # vagrant user in the guest OS. "sudo chmod 0777 /edx/src" is useful.
  :src => {:repo => "src", :local => "/edx/src", :owner => "root"},

}
if ENV['ENABLE_LEGACY_ORA']
  MOUNT_DIRS[:ora] = {:repo => "ora", :local => "/edx/app/ora/ora", :owner => "ora"}
end

if ENV['VAGRANT_MOUNT_BASE']
  MOUNT_DIRS.each { |k, v| MOUNT_DIRS[k][:repo] = ENV['VAGRANT_MOUNT_BASE'] + "/" + MOUNT_DIRS[k][:repo] }
end

# map the name of the git branch that we use for a release
# to a name and a file path, which are used for retrieving
# a Vagrant box from the internet.
openedx_releases = {
  "named-release/cypress" => {
    :name => "cypress-devstack", :file => "cypress-devstack.box",
  },
  # Birch is deprecated and unsupported
  # "named-release/birch.2" => {
  #   :name => "birch-devstack-2", :file => "birch-2-devstack.box",
  # },
}
openedx_releases.default = {
  :name => "dogwood-alpha1-devstack", :file => "dogwood-alpha1-devstack.box",
}
openedx_releases_vmware = {
  "named-release/birch" => {
    :name => "birch-devstack-vmware", :file => "20150610-birch-devstack-vmware.box",
  },
}
openedx_releases_vmware.default = {
  :name => "kifli-devstack-vmware", :file => "20140829-kifli-devstack-vmware.box",
}
rel = ENV['OPENEDX_RELEASE']

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  # Creates an edX devstack VM from an official release
  config.vm.box     = openedx_releases[rel][:name]
  config.vm.box_url = "http://files.edx.org/vagrant-images/#{openedx_releases[rel][:file]}"

  config.vm.network :private_network, ip: "192.168.33.10"
  config.vm.network :forwarded_port, guest: 8000, host: 8000  # LMS
  config.vm.network :forwarded_port, guest: 8001, host: 8001  # Studio
  config.vm.network :forwarded_port, guest: 8002, host: 8002  # Ecommerce
  config.vm.network :forwarded_port, guest: 8003, host: 8003  # LMS for Bok Choy
  config.vm.network :forwarded_port, guest: 8031, host: 8031  # Studio for Bok Choy
  config.vm.network :forwarded_port, guest: 8120, host: 8120  # edX Notes Service
  config.vm.network :forwarded_port, guest: 8765, host: 8765
  config.vm.network :forwarded_port, guest: 9200, host: 9200  # Elasticsearch
  config.vm.network :forwarded_port, guest: 18080, host: 18080  # Forums
  config.vm.network :forwarded_port, guest: 8100, host: 8100  # Analytics Data API
  config.vm.network :forwarded_port, guest: 8110, host: 8110  # Insights
  config.vm.network :forwarded_port, guest: 50070, host: 50070  # HDFS Admin UI
  config.vm.network :forwarded_port, guest: 8088, host: 8088  # Hadoop Resource Manager
  config.ssh.insert_key = true

  config.vm.synced_folder  ".", "/vagrant", disabled: true

  # Enable X11 forwarding so we can interact with GUI applications
  if ENV['VAGRANT_X11']
    config.ssh.forward_x11 = true
  end

  if ENV['VAGRANT_USE_VBOXFS'] == 'true'
    MOUNT_DIRS.each { |k, v|
      config.vm.synced_folder v[:repo], v[:local], create: true, owner: v[:owner], group: "www-data"
    }
  else
    MOUNT_DIRS.each { |k, v|
      config.vm.synced_folder v[:repo], v[:local], create: true, nfs: true
    }
  end

  config.vm.provider :virtualbox do |vb|
    vb.customize ["modifyvm", :id, "--memory", MEMORY.to_s]
    vb.customize ["modifyvm", :id, "--cpus", CPU_COUNT.to_s]

    # Allow DNS to work for Ubuntu 12.10 host
    # http://askubuntu.com/questions/238040/how-do-i-fix-name-service-for-vagrant-client
    vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
  end

  ["vmware_fusion", "vmware_workstation"].each do |vmware_provider|
    config.vm.provider vmware_provider do |v, override|
      override.vm.box     = openedx_releases_vmware[rel][:name]
      override.vm.box_url = "http://files.edx.org/vagrant-images/#{openedx_releases_vmware[rel][:file]}"
      v.vmx["memsize"] = MEMORY.to_s
      v.vmx["numvcpus"] = CPU_COUNT.to_s
    end
  end

  # Use vagrant-vbguest plugin to make sure Guest Additions are in sync
  config.vbguest.auto_reboot = true
  config.vbguest.auto_update = true

  # Assume that the base box has the edx_ansible role installed
  # We can then tell the Vagrant instance to update itself.
  config.vm.provision "shell", inline: $script, args: rel
end
