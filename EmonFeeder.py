#!/usr/bin/python

"""
Kinda-sorta-originally:

  All Emoncms code is released under the GNU Affero General Public License.
  See COPYRIGHT.txt and LICENSE.txt.

  ---------------------------------------------------------------------
  Emoncms - open source energy visualisation
  Part of the OpenEnergyMonitor project:
  http://openenergymonitor.org

Heavily modified by Fake-Name/Connor Wolf

"""

import urllib.request, urllib.error, urllib.parse, http.client
import logging, logging.handlers
import time

import logging

import sys


"""class EmonFeeder

Stores server parameters and buffers the data between two HTTP requests

"""


class EmonFeeder():

	def __init__(self, protocol, domain, path, apikey, period, testMode = False, logger=None, internalLogger = True):
		"""Create a server data buffer initialized with server settings.

		protocol (string):  "https://" or "http://"
		domain   (string):  domain name (eg: 'domain.tld')
		path     (string):  emoncms path with leading slash (eg: '/emoncms')
		apikey   (string):  API key with write access
		period   (int):     sending interval in seconds
		logger   (string):  the logger's name (default None)

		"""
		self._protocol = protocol
		self._domain = domain
		self._path = path
		self._apikey = apikey
		self._period = period
		self._data_buffer = []
		self._last_send = time.time()


		self._testMode = testMode

		if internalLogger:
			logger = self.initInternalLogging()


		self._logger = logging.getLogger(logger+".EMon")
		self._logger.debug("Initing EMonCMS interface")


	def initInternalLogging(self):
		loggerName = "Main"
		mainLogger = logging.getLogger(loggerName)			# Main logger
		mainLogger.setLevel(logging.DEBUG)

		ch = logging.StreamHandler(sys.stdout)
		formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
		ch.setFormatter(formatter)
		mainLogger.addHandler(ch)

		return loggerName


	def add_data(self, data):
		# Append timestamped dataset to buffer.
		# data (list): node and values (eg: '[node,val1,val2,...]')

		self._logger.debug("Server " + self._domain + self._path + " -> add data: " + str(data))

		self._data_buffer.append(data)

	def send_data(self):
		"""Send data to server."""
		if not self._data_buffer:
			print("Don't have any data!")
			return
		# Prepare data string with the values in data buffer
		data_string = '['
		for data in self._data_buffer:
			data_string += '['
			data_string += "0"
			for sample in data:
				data_string += ','
				data_string += str(sample)
			data_string += '],'
		data_string = data_string[0:-1]+']' # Remove trailing comma and close bracket
		self._data_buffer = []
		self._logger.debug("Data string: " + data_string)

		# Prepare URL string of the form
		# 'http://domain.tld/emoncms/input/bulk.json?apikey=12345&data=[[-10,10,1806],[-5,10,1806],[0,10,1806]]'
		url_string = self._protocol+self._domain+self._path+"/input/bulk.json?apikey="+self._apikey+"&data="+data_string
		self._logger.debug("URL string: " + url_string)

		# Send data to server
		self._logger.info("Sending to " + self._domain + self._path)
		if not self._testMode:
			try:
				result = urllib.request.urlopen(url_string)
			except urllib.error.HTTPError as e:
				self._logger.warning("Couldn't send to server, HTTPError: " + str(e.code))
			except urllib.error.URLError as e:
				self._logger.warning("Couldn't send to server, URLError: " + str(e.reason))
			except http.client.HTTPException:
				self._logger.warning("Couldn't send to server, HTTPException")
			except Exception:
				import traceback
				self._logger.warning("Couldn't send to server, Exception: " + traceback.format_exc())
			else:
				if (result.readline().decode("ascii") == 'ok'):
					self._logger.info("Send ok")
				else:
					self._logger.critical("Send failure")
		else:
			print("Test mode! Not actually sending")

		# Update _last_send
		#self._last_send = time.time()

	def send_node_data(self, nodeid, data, time=False):
		"""Send data to server."""

		# Prepare data string with the values in data buffer
		data_string = 'csv='
		for item in data:
			data_string += str(item)
			data_string += ','

		data_string = data_string[0:-1]  # Remove trailing comma

		self._logger.debug("Data string: " + data_string)

		# Prepare URL string of the form
		# 'http://domain.tld/emoncms/input/bulk.json?apikey=12345&data=[[-10,10,1806],[-5,10,1806],[0,10,1806]]'
		url_string = self._protocol+self._domain+self._path+"/input/post.json?apikey="+self._apikey+"&node="+str(nodeid)+"&"+data_string
		if time:
			url_string += "&time="+str(time)
		self._logger.debug("URL string: " + url_string)

		# Send data to server
		self._logger.info("Sending to " + self._domain + self._path)

		try:
			result = urllib.request.urlopen(url_string)
		except urllib.error.HTTPError as e:
			self._logger.warning("Couldn't send to server, HTTPError: " + str(e.code))
		except urllib.error.URLError as e:
			self._logger.warning("Couldn't send to server, URLError: " + str(e.reason))
		except http.client.HTTPException:
			self._logger.warning("Couldn't send to server, HTTPException")
		except Exception:
			import traceback
			self._logger.warning("Couldn't send to server, Exception: " + traceback.format_exc())
		else:
			if (result.readline() == 'ok'):
				self._logger.info("Send ok")
			else:
				self._logger.warning("Send failure")

		# Update _last_send
		#self._last_send = time.time()

	def check_time(self):
		"""Check if it is time to send data to server.

		Return True if sending interval has passed since last time

		"""
		now = time.time()
		delta = now - self._last_send
		if (delta > self._period):
			print(("Elapsed delta between updates =", delta, "seconds. overshoot =", delta-self._period, "seconds."))
			self._last_send = self._last_send + self._period
			return True

	def has_data(self):
		"""Check if buffer has data

		Return True if data buffer is not empty.

		"""
		return (self._data_buffer != [])