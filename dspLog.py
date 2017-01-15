#!/usr/bin/python


import time
import urllib.parse
import urllib.request
import random
import logging

import EmonFeeder

DSP_OUTLETS = [
		# Add more outlets here. The first number is the node number sent to emoncms,
		# the second value is the IP address for the specified node.
		(2, '10.1.2.200'),
]

# The graphite storage engine averages the values if you send several samples
# in a single logging interval. I have no idea how emoncms's silly PHP reimplementation
# works (because it's a stupid idea).
# Anyways, oversampling is better then undersampling.
UPDATE_INTERVAL_SECONDS = 5

class DSPInterface(object):
	def __init__(self, plugIp):
		self.ip = plugIp
		self.log = logging.getLogger("Main.Plug-{}".format(self.ip))


	def getReading(self):

		postData_dict = {'request': 'create_chklst'}
		postData = urllib.parse.urlencode(postData_dict).encode("ascii")

		req = urllib.request.Request("http://{ip}/my_cgi.cgi?{rand}".format(ip=self.ip, rand=str(random.random())), data=postData)
		response = urllib.request.urlopen(req)
		ret = response.read().decode("utf-8")
		ret = ret.strip()
		lines = ret.split("\n")

		retVal = None

		for line in lines:
			if line.startswith("Meter Watt:"):
				power = line.split()[-1]
				if retVal:
					raise ValueError("Two power readings in one response?")
				try:
					retVal = float(power)
				except ValueError:
					self.log.error("Error on string '%s'", line)
					return None

		if not retVal:
			self.log.error("WARNING: Outlet API request returned no data!")
			self.log.error("Request URL: '%s'", req)
			self.log.error("Outlet response:")
			self.log.error("%s", ret)
			return None
		return retVal


def get_key():
	paths = [
		"../emoncmsApiKey.conf",
		"./emoncmsApiKey.conf"
	]

	for pathn in paths:
		try:
			apiKey = open(pathn, "r").read()
			return apiKey
		except FileNotFoundError:
			pass

	raise RuntimeError("No API key file found! This script expects the api key in a text file named `emoncmsApiKey.conf`,"+
		" in either the current directory or one directory above the current dir!")



if __name__ == "__main__":
	print("Starting")



	monBuf = EmonFeeder.EmonFeeder(protocol = 'https://',
							  domain = '10.1.1.39',
							  path = '/emoncms',
							  apikey = get_key(),
							  period = 15)
	outlets = []
	for nodenum, nodeip in DSP_OUTLETS:
		outlets.append((nodenum, DSPInterface(nodeip)))
	print("Plugs opened: %s" % outlets)


	nextRun = time.time() + UPDATE_INTERVAL_SECONDS
	while 1:
		try:
			for outletid, outlet in outlets:
				powerReading = outlet.getReading()

				if powerReading is not None:
					print("Have data (%s watts)! Ready to send" % (powerReading, ))

					# I don't remember what this zero is here for.
					monBuf.add_data([str(outletid), 0, powerReading])
				else:
					print("Outlet %s did not return data (%s)!" % (outletid, outlet))
			monBuf.send_data()
		except:
			raise

		while time.time() < nextRun:
			time.sleep(1)
		nextRun += UPDATE_INTERVAL_SECONDS
		print("LOOPIN")
