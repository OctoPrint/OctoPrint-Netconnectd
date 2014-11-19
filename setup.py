# coding=utf-8
import setuptools

def package_data_dirs(source, sub_folders):
	import os
	dirs = []

	for d in sub_folders:
		for dirname, _, files in os.walk(os.path.join(source, d)):
			dirname = os.path.relpath(dirname, source)
			for f in files:
				dirs.append(os.path.join(dirname, f))

	return dirs

def params():
	name = "OctoPrint-Netconnectd"
	version = "0.1"

	description = "Client for netconnectd that allows configuration of netconnectd through OctoPrint's settings dialog. It's only available for Linux right now."
	author = "Gina Häußge"
	author_email = "osd@foosel.net"
	url = "http://octoprint.org"
	license = "AGPLv3"

	packages = ["octoprint_netconnectd"]
	package_data = {"octoprint_netconnectd": package_data_dirs('octoprint_netconnectd', ['static', 'templates'])}

	include_package_data = True
	zip_safe = False
	install_requires = open("requirements.txt").read().split("\n")

	entry_points = {
		"octoprint.plugin": [
			"netconnectd = octoprint_netconnectd"
		]
	}

	return locals()

setuptools.setup(**params())
