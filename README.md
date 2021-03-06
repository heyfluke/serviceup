serviceup
=========

A simple service monitoring daemon written in Python, forked from jstarcher/serviceup.
* builtin monitoring function for http/https.
* extensable monitoring for other kinds of protocols.
* view status from builtin web server.

## Usage

### basic usage
1. Configuration is super easy. Follow the examples in config.ini to setup your own services. (copy config-dist.ini to config.ini first.)
2. Start the daemon with ./serviceup.py start

#### configurations

##### http
* get url and find some string in the content.
	* url = str (eg. mydomain.com:8080)
	* content = str  (eg. running)
##### https
* same as http

##### tcp_port
* just test whether the port is reachable.
	* host
	* port

### Advanced usage

#### write your own plugin to support more protocols.

* put your python module inside plugins folder.
* there is a ready to use dns monitor inside plugins/. (you need to install dnspython first - pip install dnspython.)

#### plugin protocol

* plugin must implement a plugin_entry(**kwds) function, return True for succ.
* plugin must beed put in plugins/ folder.
* config plugin like this:

	[check dns using plugin dnsmonitor]
	  [[plugin_dnsmonitor]]
	  hostname = 'www.github.com'
	  nameserver = '8.8.8.8'

* serviceup.py pass config parameters as **kwds to the plugin_entry function.

### other tuning
By default the daemon will check each service every 5 minutes. The frequency can easily be changed in
serviceup.py. There are several advanced cofiguration variables in serviceup.py which can be configured
to your liking. For example: the from email address, log directory, etc.
