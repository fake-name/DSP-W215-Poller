#!/usr/bin/python


import EmonFeeder
import time
import urllib.parse
import urllib.request
import random

DSP_OUTLET_IP = '10.1.2.200'
UPDATE_INTERVAL = 5

class DSPInterface(object):
	def __init__(self, plugIp):
		self.ip = plugIp

	def getReading(self):
		pass

		postData = {'request': 'create_chklst'}
		postData = urllib.parse.urlencode(postData).encode("ascii")

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
					print("Error on string '%s'" % line)
					return None

		return retVal



if __name__ == "__main__":
	print("Starting")


	apiKey = open("../emoncmsApiKey.conf", "r").read()

	monBuf = EmonFeeder.EmonFeeder(protocol = 'https://',
							  domain = '10.1.1.39',
							  path = '/emoncms',
							  apikey = apiKey,
							  period = 15)

	outlet = DSPInterface(DSP_OUTLET_IP)
	print("Plug opened. Handle = %s" % outlet)


	nextRun = time.time() + UPDATE_INTERVAL
	while 1:
		try:
			powerReading = outlet.getReading()

			if powerReading:
				print("Have data! Ready to send")
				monBuf.add_data(["2", 0, powerReading])
				monBuf.send_data()
		except:
			raise

		while time.time() < nextRun:
			time.sleep(1)
		nextRun += UPDATE_INTERVAL
		print("LOOPIN")
