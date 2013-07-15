MEMORY = 512
CPU_COUNT = 2

Vagrant.configure("2") do |config|
  config.vm.box     = "precise64"
  config.vm.box_url = "http://files.vagrantup.com/precise64.box"

  config.vm.network :private_network, ip: "192.168.111.222"

  config.vm.provider :virtualbox do |vb|
    vb.customize ["modifyvm", :id, "--memory", MEMORY.to_s]

    # You can adjust this to the amount of CPUs your system has available
    vb.customize ["modifyvm", :id, "--cpus", CPU_COUNT.to_s]
  end

  config.vm.provision :ansible do |ansible|
    # point Vagrant at the location of your playbook you want to run
    ansible.playbook = "playbooks/vagrant.yml"

    ansible.inventory_file = "playbooks/vagrant/inventory.ini"
    ansible.extra_vars = { secure_dir: "secure_example" }
    ansible.verbose = true
  end
end
