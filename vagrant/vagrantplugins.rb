# Don't check for plugins on certain subcommands of vagrant.
def is_check_necessary
    exempt = ['help', 'plugin', 'version']
    return ARGV.any? ? (ARGV & exempt).empty? : false
end

def install_plugins(plugins)
    if not is_check_necessary
	exit
    end

    not_installed = get_not_installed(plugins)
    if not_installed.any?
	puts "The following required plugins must be installed:"
	puts "'#{not_installed.join("', '")}'"
	print "Install? [y]/n: "
	unless STDIN.gets.chomp == "n"
	    not_installed.each { |plugin| install_plugin(plugin) }
    	else
      	    exit
    	end
    	$? ? continue : raise('Plugin installation failed, see errors above.')
    end
end

def get_not_installed(plugins)
    not_installed = []
    plugins.each do |plugin|
	unless Vagrant.has_plugin?(plugin)
	    not_installed << plugin
        end
    end
    return not_installed
end

def install_plugin(plugin)
    system "vagrant plugin install #{plugin}"
end

# If plugins successfully installed, restart vagrant to detect changes.
def continue
    exec "vagrant #{ARGV.join(' ')}"
end

