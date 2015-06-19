# coding=utf-8
from __future__ import absolute_import

__author__ = "Gina Häußge <osd@foosel.net>"
__license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'
__copyright__ = "Copyright (C) 2014 The OctoPrint Project - Released under terms of the AGPLv3 License"


import logging
from flask import jsonify, make_response

import octoprint.plugin

from octoprint.server import admin_permission

class NetconnectdSettingsPlugin(octoprint.plugin.SettingsPlugin,
                                octoprint.plugin.TemplatePlugin,
                                octoprint.plugin.SimpleApiPlugin,
                                octoprint.plugin.AssetPlugin):

	def __init__(self):
		self.address = None

	def initialize(self):
		self.address = self._settings.get(["socket"])

	@property
	def hostname(self):
		hostname = self._settings.get(["hostname"])
		if hostname:
			return hostname
		else:
			import socket
			return socket.gethostname() + ".local"

	##~~ SettingsPlugin

	def on_settings_save(self, data):
		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
		self.address = self._settings.get(["socket"])

	def get_settings_defaults(self):
		return dict(
			socket="/var/run/netconnectd.sock",
			hostname=None,
			timeout=10
		)

	##~~ TemplatePlugin API

	def get_template_configs(self):
		return [
			dict(type="settings", name="Network connection")
		]

	##~~ SimpleApiPlugin API

	def get_api_commands(self):
		return dict(
			start_ap=[],
			stop_ap=[],
			refresh_wifi=[],
			configure_wifi=[],
			forget_wifi=[],
			reset=[]
		)

	def is_api_adminonly(self):
		return True

	def on_api_get(self, request):
		try:
			status = self._get_status()
			if status["wifi"]["present"]:
				wifis = self._get_wifi_list()
			else:
				wifis = []
		except Exception as e:
			return jsonify(dict(error=e.message))

		return jsonify(dict(
			wifis=wifis,
			status=status,
			hostname=self.hostname
		))

	def on_api_command(self, command, data):
		if command == "refresh_wifi":
			return jsonify(self._get_wifi_list(force=True))

		# any commands processed after this check require admin permissions
		if not admin_permission.can():
			return make_response("Insufficient rights", 403)

		if command == "configure_wifi":
			if data["psk"]:
				self._logger.info("Configuring wifi {ssid} and psk...".format(**data))
			else:
				self._logger.info("Configuring wifi {ssid}...".format(**data))

			self._configure_and_select_wifi(data["ssid"], data["psk"], force=data["force"] if "force" in data else False)

		elif command == "forget_wifi":
			self._forget_wifi()

		elif command == "reset":
			self._reset()

		elif command == "start_ap":
			self._start_ap()

		elif command == "stop_ap":
			self._stop_ap()

	##~~ AssetPlugin API

	def get_assets(self):
		return dict(
			js=["js/netconnectd.js"],
			css=["css/netconnectd.css"],
			less=["less/netconnectd.less"]
		)

	##~~ Private helpers

	def _get_wifi_list(self, force=False):
		payload = dict()
		if force:
			self._logger.info("Forcing wifi refresh...")
			payload["force"] = True

		flag, content = self._send_message("list_wifi", payload)
		if not flag:
			raise RuntimeError("Error while listing wifi: " + content)

		result = []
		for wifi in content:
			result.append(dict(ssid=wifi["ssid"], address=wifi["address"], quality=wifi["signal"], encrypted=wifi["encrypted"]))
		return result

	def _get_status(self):
		payload = dict()

		flag, content = self._send_message("status", payload)
		if not flag:
			raise RuntimeError("Error while querying status: " + content)

		return content

	def _configure_and_select_wifi(self, ssid, psk, force=False):
		payload = dict(
			ssid=ssid,
			psk=psk,
			force=force
		)

		flag, content = self._send_message("config_wifi", payload)
		if not flag:
			raise RuntimeError("Error while configuring wifi: " + content)

		flag, content = self._send_message("start_wifi", dict())
		if not flag:
			raise RuntimeError("Error while selecting wifi: " + content)

	def _forget_wifi(self):
		payload = dict()
		flag, content = self._send_message("forget_wifi", payload)
		if not flag:
			raise RuntimeError("Error while forgetting wifi: " + content)

	def _reset(self):
		payload = dict()
		flag, content = self._send_message("reset", payload)
		if not flag:
			raise RuntimeError("Error while factory resetting netconnectd: " + content)

	def _start_ap(self):
		payload = dict()
		flag, content = self._send_message("start_ap", payload)
		if not flag:
			raise RuntimeError("Error while starting ap: " + content)

	def _stop_ap(self):
		payload = dict()
		flag, content = self._send_message("stop_ap", payload)
		if not flag:
			raise RuntimeError("Error while stopping ap: " + content)

	def _send_message(self, message, data):
		obj = dict()
		obj[message] = data

		import json
		js = json.dumps(obj, encoding="utf8", separators=(",", ":"))

		import socket
		sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		sock.settimeout(self._settings.get_int(["timeout"]))
		try:
			sock.connect(self.address)
			sock.sendall(js + '\x00')

			buffer = []
			while True:
				chunk = sock.recv(16)
				if chunk:
					buffer.append(chunk)
					if chunk.endswith('\x00'):
						break

			data = ''.join(buffer).strip()[:-1]

			response = json.loads(data.strip())
			if "result" in response:
				return True, response["result"]

			elif "error" in response:
				# something went wrong
				self._logger.warn("Request to netconnectd went wrong: " + response["error"])
				return False, response["error"]

			else:
				output = "Unknown response from netconnectd: {response!r}".format(response=response)
				self._logger.warn(output)
				return False, output

		except Exception as e:
			output = "Error while talking to netconnectd: {}".format(e.message)
			self._logger.warn(output)
			return False, output

		finally:
			sock.close()

__plugin_name__ = "Netconnectd Client"

def __plugin_check__():
	import sys
	if sys.platform == 'linux2':
		return True

	logging.getLogger("octoprint.plugins." + __name__).warn("The netconnectd plugin only supports Linux")
	return False

def __plugin_load__():
	# since we depend on a Linux environment, we instantiate the plugin implementation here since this will only be
	# called if the OS check above was successful
	global __plugin_implementation__
	__plugin_implementation__ = NetconnectdSettingsPlugin()
	return True



