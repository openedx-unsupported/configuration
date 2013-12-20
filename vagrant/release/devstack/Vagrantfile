MEMORY = 2048
CPU_COUNT = 2

$script = <<SCRIPT
source /edx/app/edx_ansible/venvs/edx_ansible/bin/activate
cd /edx/app/edx_ansible/edx_ansible/playbooks
ansible-playbook -i localhost, -c local vagrant-devstack.yml
SCRIPT

edx_platform_mount_dir = "edx-platform"
forum_mount_dir = "cs_comments_service"
ora_mount_dir = "ora"

if ENV['VAGRANT_MOUNT_BASE']

  edx_platform_mount_dir = ENV['VAGRANT_MOUNT_BASE'] + "/" + edx_platform_mount_dir
  forum_mount_dir = ENV['VAGRANT_MOUNT_BASE'] + "/" + forum_mount_dir
  ora_mount_dir = ENV['VAGRANT_MOUNT_BASE'] + "/" + ora_mount_dir

end

Vagrant.configure("2") do |config|

  # Creates an edX devstack VM from an official release
  config.vm.box     = "empanada-devstack"
  config.vm.box_url = "http://edx-static.s3.amazonaws.com/vagrant-images/20131219-empanada-devstack.box"

  config.vm.network :private_network, ip: "192.168.33.10"
  config.vm.network :forwarded_port, guest: 8000, host: 8000
  config.vm.network :forwarded_port, guest: 8001, host: 8001
  config.vm.network :forwarded_port, guest: 4567, host: 4567

  config.vm.synced_folder "#{edx_platform_mount_dir}", "/edx/app/edxapp/edx-platform", :create => true, nfs: true
  config.vm.synced_folder "#{forum_mount_dir}", "/edx/app/forum/cs_comments_service", :create => true, nfs: true
  config.vm.synced_folder "#{ora_mount_dir}", "/edx/app/ora/ora", :create => true, nfs: true

  config.vm.provider :virtualbox do |vb|
    vb.customize ["modifyvm", :id, "--memory", MEMORY.to_s]
    vb.customize ["modifyvm", :id, "--cpus", CPU_COUNT.to_s]

    # Allow DNS to work for Ubuntu 12.10 host
    # http://askubuntu.com/questions/238040/how-do-i-fix-name-service-for-vagrant-client
    vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
  end

  # Assume that the base box has the edx_ansible role installed
  # We can then tell the Vagrant instance to update itself.
  config.vm.provision "shell", inline: $script

end
