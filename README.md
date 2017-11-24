---

Provided as-is, currently not actively maintained.

[OctoPrint](http://octoprint.org) is eating up too much of my time and I don't find myself at liberty to actively maintain this project for the foreseeable future. If it works for you, great. If it doesn't, sorry, I can't look into it.

---

# netconnectd plugin for OctoPrint

![netconnectd plugin: Overview with list of available wifis](https://i.imgur.com/Yjmxypvl.png)

![netconnectd plugin: Configuration of secured wifi](https://i.imgur.com/NIjPBYpl.png)

This is a plugin for OctoPrint that acts as a client for the [netconnect](https://github.com/foosel/netconnectd) linux
daemon. It allows visualizing the status of the current network connection, viewing the available Wifi networks
and connecting to a Wifi network (including entering necessary network credentials).

It depends on OctoPrint version 1.2.0-dev-195 and up.

The plugin will try to automatically reconnect when switching from netconnectd's ap mode to a known network. In order
to do that, it assumes that the client host will switch to the same network as the OctoPrint instance once the access
point goes down and that the OctoPrint instance will be available as `<hostname>.local` after the switch (so the host
running OctoPrint will need to be configured with [support for .local domains](https://en.wikipedia.org/wiki/.local)). 
If the client/browser doing the configuration is running on Windows, [Bonjour for Windows](http://support.apple.com/kb/DL999) will need to be installed 
for this to seamlessly work (it comes bundled with the iTunes installed which you simply unzip to get at it but 
alternatively take a look at [this entry in the OctoPrint wiki](https://github.com/foosel/OctoPrint/wiki/Setup-on-a-Raspberry-Pi-running-Raspbian#reach-your-printer-by-typing-its-name-in-address-bar-of-your-browser---avahizeroconfbonjour-based)). 
For Linux clients, Avahi will need to be installed, including the libdnssd compatibility layer (`libavahi-compat-libdnssd1` 
in Ubuntu).

## Setup

First setup [netconnect](https://github.com/foosel/netconnectd) like described in its [README](https://github.com/foosel/netconnectd/blob/master/README.md). 
Without that daemon setup on the system serving as your OctoPrint host, the plugin won't work.

After that, just install the plugin like you would install any regular Python package from source:

    pip install https://github.com/OctoPrint/OctoPrint-Netconnectd/archive/master.zip

Make sure you use the same Python environment that you installed OctoPrint under, otherwise the plugin won't be able
to satisfy its dependencies.

Restart OctoPrint. `octoprint.log` should show you that the plugin was successfully found and loaded:

    2014-09-11 17:45:26,572 - octoprint.plugin.core - INFO - Loading plugins from ... and installed plugin packages...
    2014-09-11 17:45:26,648 - octoprint.plugin.core - INFO - Found 2 plugin(s): netconnectd client (0.1), Discovery (0.1)

## Configuration

The plugin has two configuration options that due to their sensitivity are not configurable via the web interface right
now, you'll have to edit OctoPrint's `config.yaml` directly: 

    plugins:
      netconnectd:
        # The location of the unix domain socket provided by netconnectd. Defaults to /var/run/netconnectd.sock, which
        # is also netconnectd's default value.
        socket: /var/run/netconnectd.sock
        
        # The hostname to try to reach after switching from AP mode to wifi connection. If left unset, OctoPrint will
        # automatically attempt to connect to <hostname>.local. Defaults to not set.
        hostname: someothername.local
