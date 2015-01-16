# coding=utf-8
from __future__ import absolute_import

__author__ = "Gina Häußge <osd@foosel.net>"
__license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'
__copyright__ = "Copyright (C) 2014 The OctoPrint Project - Released under terms of the AGPLv3 License"


import os
import logging
from flask import jsonify

import octoprint.plugin


default_settings = {
	"socket": "/var/run/netconnectd.sock",
	"hostname": None
}
s = octoprint.plugin.plugin_settings("netconnectd", defaults=default_settings)


class NetconnectdSettingsPlugin(octoprint.plugin.SettingsPlugin,
                                octoprint.plugin.TemplatePlugin,
                                octoprint.plugin.SimpleApiPlugin,
                                octoprint.plugin.AssetPlugin):

	def __init__(self):
		self.logger = logging.getLogger("plugins.netconnectd." + __name__)
		self.address = s.get(["socket"])

	@property
	def hostname(self):
		if s.get(["hostname"]):
			return s.get(["hostname"])
		else:
			import socket
			return socket.gethostname() + ".local"

	##~~ SettingsPlugin

	def on_settings_load(self):
		return {
			"socket": s.get(["socket"]),
			"hostname": s.get(["hostname"])
		}

	def on_settings_save(self, data):
		if "socket" in data and data["socket"]:
			s.set(["socket"], data["socket"])
		if "hostname" in data and data["hostname"]:
			s.set(["hostname"], data["hostname"])

		self.address = s.get(["socket"])

	##~~ TemplatePlugin API

	def get_template_configs(self):
		return [
			dict(type="settings", name="Network connection")
		]

	##~~ SimpleApiPlugin API

	def get_api_commands(self):
		return {
			"start_ap": [],
			"stop_ap": [],
			"refresh_wifi": [],
			"configure_wifi": ["ssid", "psk"],
			"forget_wifi": [],
			"reset": []
		}

	def on_api_get(self, request):
		try:
			wifis = self._get_wifi_list()
			status = self._get_status()
		except Exception as e:
			return jsonify(dict(error=e.message))

		return jsonify({
			"wifis": wifis,
			"status": status,
			"hostname": self.hostname
		})

	def on_api_command(self, command, data):
		if command == "refresh_wifi":
			return jsonify(self._get_wifi_list(force=True))

		elif command == "configure_wifi":
			if data["psk"]:
				self.logger.info("Configuring wifi {ssid} and psk...".format(**data))
			else:
				self.logger.info("Configuring wifi {ssid}...".format(**data))

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
		return {
			"js": ["js/netconnectd.js"],
			"css": ["css/netconnectd.css"],
			"less": ["less/netconnectd.less"]
		}

	##~~ Private helpers

	def _get_wifi_list(self, force=False):
		payload = dict()
		if force:
			self.logger.info("Forcing wifi refresh...")
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
		sock.settimeout(10)
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
				self.logger.warn("Request to netconnectd went wrong: " + response["error"])
				return False, response["error"]

			else:
				output = "Unknown response from netconnectd: {response!r}".format(response=response)
				self.logger.warn(output)
				return False, output

		except Exception as e:
			output = "Error while talking to netconnectd: {}".format(e.message)
			self.logger.warn(output)
			return False, output

		finally:
			sock.close()

__plugin_name__ = "netconnectd client"
__plugin_version__ = "0.1"
__plugin_description__ = "Client for netconnectd that allows configuration of netconnectd through OctoPrint's settings dialog"
__plugin_implementations__ = []

def __plugin_check__():
	import sys
	if not sys.platform == 'linux2':
		logging.getLogger("octoprint.plugins." + __name__).warn("The netconnectd plugin only supports Linux")
		return False

	global __plugin_implementations__
	__plugin_implementations__ = [NetconnectdSettingsPlugin()]
	return True



