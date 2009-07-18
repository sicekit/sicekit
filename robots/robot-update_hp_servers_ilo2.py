#!/usr/bin/python
# -*- coding: utf-8  -*-
"""

"""
import wikipedia
import pagegenerators, catlib, re, socket, sys
import base64
import struct

class ILO2InventoryBot:

	def __init__(self, hosts_generator):
		self.hosts_generator = hosts_generator

	def run(self):
		for page in self.hosts_generator:
			if not "." in page.title(): continue
			self.processpage(page)

	def processpage(self, page):
		wikipedia.setAction(u'Robot: update hardware inventory')
		print page.title()
		oldlines = page.get().split("\r\n")
		newlines = list()
		data = dict()
		# find ILO IP, and fetch data
		for line in oldlines:
			if not line.startswith("|OOBIP="): continue
			oobip = line.split("=")[1].replace("\r","")
			print repr(oobip)
			if oobip == "": continue
			data = self.fetchIloData(oobip)
			break

		# do string formatting for RAMUSED
		if data.has_key('ram'):
			sizescount = dict()
			for rammodule in data['ram']:
				# ignore empty banks
				if rammodule['size'] == 0: continue
				if not sizescount.has_key(rammodule['size']): sizescount[rammodule['size']] = 0
				sizescount[rammodule['size']] = sizescount[rammodule['size']] + 1
			sizes = sizescount.keys()
			sizes.sort(reverse=True)
			ram = list()
			for size in sizes:
				ram.append('%dx %dMB' % (sizescount[size], size))
			data['ram'] = " + ".join(ram)

		if data.has_key('cpus'):
			cputypes = dict()
			for i in range(0, data['cpus']):
				cputype = data['cpu'+str(i+1)]
				if not cputypes.has_key(cputype): cputypes[cputype] = 0
				cputypes[cputype] += 1

			cpu = []
			types = cputypes.keys()
			types.sort()
			for cputype in types:
				cpu.append('%dx %s' % (cputypes[cputype], cputype))
			data['cpu'] = ", ".join(cpu)

		# now replace the values
		for line in oldlines:
			if line.startswith("|SN=") and data.has_key('serialnumber'):
				line = "|SN=" + data['serialnumber']
				del data['serialnumber']
			if line.startswith("|PN=") and data.has_key('skunumber'):
				line = "|PN=" + data['skunumber']
				del data['skunumber']
			if line.startswith("|OOBMAC") and data.has_key('oobmac'):
				line = "|OOBMAC=" + data['oobmac']
				del data['oobmac']
			if line.startswith("|RAMUSED") and data.has_key('ram'):
				line = "|RAMUSED=" + data['ram']
				del data['ram']
			if line.startswith("|CPUUSED") and data.has_key('cpu'):
				line = "|CPUUSED=" + str(data['cpu'])
				del data['cpu']
			if line.startswith("|RPSUSED") and data.has_key('rpsused'):
				line = "|RPSUSED=" + str(data['rpsused'])
				del data['rpsused']
			if line.startswith("|NICMAC1") and data.has_key('nicmac1'):
				line = "|NICMAC1=" + str(data['nicmac1'])
				del data['nicmac1']
			if line.startswith("|NICMAC2") and data.has_key('nicmac2'):
				line = "|NICMAC2=" + str(data['nicmac2'])
				del data['nicmac2']

			if line.startswith("}}"):
				# hardware template is over, add probably missing lines
				if data.has_key('skunumber'): newlines.append("|PN=" + data['skunumber'])
				if data.has_key('rpsused'): newlines.append("|RPSUSED=" + str(data['rpsused']))
				# now ensure that no other changes are made
				data = dict()
			newlines.append(line)
		pagetext = "\r\n".join(newlines)

		# save, if there are differences
		if page.get() == pagetext: return
		wikipedia.showDiff(page.get(), pagetext)
		# Save the page
		try:
			page.put(pagetext)
		except wikipedia.LockedPage:
			wikipedia.output(u"Page %s is locked; skipping." % page.aslink())
		except wikipedia.EditConflict:
			wikipedia.output(u'Skipping %s because of edit conflict' % (page.title()))
		except wikipedia.SpamfilterError, error:
			wikipedia.output(u'Cannot change %s because of spam blacklist entry %s' % (page.title(), error.url))

	def fetchIloData(self, iloaddress):
		results = dict()
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			sock.connect((iloaddress, 443))
		except socket.gaierror:
			return results
		except socket.error:
			return results
		s = socket.ssl(sock)
		xml_header = '<?xml version="1.0"?>'
		xml = """<RIBCL version="2.21">
<LOGIN USER_LOGIN="%s" PASSWORD="%s">
<SERVER_INFO MODE="READ" >
<GET_HOST_DATA />
<GET_EMBEDDED_HEALTH />
</SERVER_INFO>
<RIB_INFO MODE="read">
<GET_NETWORK_SETTINGS/>
</RIB_INFO>
</LOGIN>
</RIBCL>
"""
		xml = xml_header + "\n" + (xml % (wikipedia.config.bot_hpilo2_ilo_username, wikipedia.config.bot_hpilo2_ilo_password))
		for line in xml.split("\n"):
			s.write(line + "\r\n")
		data = ""
		while True:
			try:
				data = data + s.read()
				if "</RIB_INFO>" in data: break
			except socket.sslerror:
				break
		del s
		sock.close()

		# pre`split data
		data = data.split("\n")

		# preprocess hostdata, save away cache structs
		in_host_data = False
		cachestructs = {}
		for line in data:
			if '<GET_HOST_DATA>' in line:
				in_host_data = True
				continue
			if '</GET_HOST_DATA>' in line:
				in_host_data = False
				continue
			if not in_host_data: continue

			if not '<SMBIOS_RECORD ' in line: continue
			smbios_data = line.split("B64_DATA=\"")[1].split("\"")[0]
			smbios_data = base64.b64decode(smbios_data)
			if 'TYPE="7"' in line:
				this = dict()
				handle = struct.unpack('H', smbios_data[0x2:0x4])[0]
				size = struct.unpack('H', smbios_data[0x9:0xB])[0] & 0xFF
				size = size * 64
				cachestructs[handle] = size

		# now process data
		in_host_data = False
		for line in data:
			if '<GET_HOST_DATA>' in line:
				in_host_data = True
				continue
			if '</GET_HOST_DATA>' in line:
				in_host_data = False
				continue
			if not in_host_data: continue

			if not '<SMBIOS_RECORD ' in line: continue
			smbios_data = line.split("B64_DATA=\"")[1].split("\"")[0]
			smbios_data = base64.b64decode(smbios_data)
			if 'TYPE="1"' in line:
				# System ID
				this = dict()
				# byte 0 is the type, MUST be 1
				# byte 1 is the length, on HP machines I've only observed 0x19 (SMBIOS v2.1-2.3.4) or 0x1Bh (2.4 or latter)
				length = ord(smbios_data[0x1])
				strings = smbios_data[length:].split("\x00")
				# byte 5 is the productname (string#)
				self.from_smbios_string('productname', smbios_data, strings, length, 0x5, this)
				# byte 6 is the version (string#)
				self.from_smbios_string('version', smbios_data, strings, length, 0x6, this)
				# byte 7 is the serialnumber (string#)
				self.from_smbios_string('serialnumber', smbios_data, strings, length, 0x7, this)
				# byte 8 is the uuid (16 bytes)
				# byte 19 is the sku number (string#)
				self.from_smbios_string('skunumber', smbios_data, strings, length, 0x19, this)
				# byte 1a is the family (string#)
				self.from_smbios_string('family', smbios_data, strings, length, 0x1a, this)
				results.update(this)
			if 'TYPE="4"' in line:
				# CPU
				length = ord(smbios_data[0x1])
				strings = smbios_data[length:].split("\x00")
				if smbios_data[0x16] == '\x00' and smbios_data[0x17] == '\x00':
					# no cpu present
					pass
				else:
					this = dict()
					self.from_smbios_string('socketname', smbios_data, strings, length, 0x4, this)
					self.from_smbios_string('vendor', smbios_data, strings, length, 0x7, this)
					this['cores'] = ord(smbios_data[0x23])
					if this['cores'] == 2: this['corestr'] = 'Dual-Core'
					if this['cores'] == 4: this['corestr'] = 'Quad-Core'
					this['cpufamily'] = ord(smbios_data[0x6])
					if this['cpufamily'] == 0xb3: this['cpufamstr'] = 'Xeon'
					this['fsb'] = struct.unpack('H', smbios_data[0x12:0x14])[0]
					this['speed'] = struct.unpack('H', smbios_data[0x16:0x18])[0]
					this['sockettype'] = ord(smbios_data[0x19])
					if this['sockettype'] == 0x15: this['socketstr'] = 'LGA775'
					if this['sockettype'] == 0x14: this['socketstr'] = 'LGA771'
					this['l2cachesize'] = cachestructs[struct.unpack('H', smbios_data[0x1C:0x1E])[0]]

					# this is mad guesswork.
					if this['cpufamily'] == 0xb3 and this['fsb'] == 1066:
						if this['cores'] == 2 and this['l2cachesize'] == 4096:
							if this['speed'] == 2400: this['model'] = '3060'

					if this['cpufamily'] == 0xb3 and this['fsb'] == 1333:
						if this['cores'] == 2 and this['l2cachesize'] == 4096:
							if this['speed'] == 2000: this['model'] = '5130'
							if this['speed'] == 2333: this['model'] = '5140'
							if this['speed'] == 2666: this['model'] = '5150'
							if this['speed'] == 3000: this['model'] = '5160'
						if this['cores'] == 4:
							if this['l2cachesize'] == 8192:
								if this['speed'] == 2000: this['model'] = 'E5335'
								if this['speed'] == 2333: this['model'] = 'E5345'
							if this['l2cachesize'] == 12288:
								if this['speed'] == 2000: this['model'] = 'E5405'
								if this['speed'] == 2333: this['model'] = 'E5410'
								if this['speed'] == 2500: this['model'] = 'E5420'
								if this['speed'] == 2666: this['model'] = 'E5430'
								if this['speed'] == 2833: this['model'] = 'E5440'
								if this['speed'] == 3000: this['model'] = 'E5450'

					if not this.has_key('model'):
						print 'Unknown CPU, details: speed=%s, cores=%s, fsb=%s, family=%x, l2cache=%s' % (this['speed'], this['cores'], this['fsb'], this['cpufamily'], this['l2cachesize'])
						this['model'] = 'UnknownCPU'

					if not results.has_key('cpus'): results['cpus'] = 0
					results['cpus'] += 1
					thiscpu = 'cpu' + str(results['cpus'])
					results[thiscpu] = '%s %s %s %s' % (this['vendor'], this['corestr'], this['cpufamstr'], this['model'])
			if 'TYPE="17"' in line:
				# Memory
				this = dict()
				length = ord(smbios_data[0x1])
				strings = smbios_data[length:].split("\x00")
				self.from_smbios_string('device_locator', smbios_data, strings, length, 0x10, this)
				self.from_smbios_string('bank_locator', smbios_data, strings, length, 0x11, this)
				this['size'] = struct.unpack('H', smbios_data[0x0c:0x0e])[0]
				if not results.has_key('ram'):
					results['ram'] = list()
				results['ram'].append(this)
			if 'TYPE="209"' in line:
				# NIC Ethernet Addresses
				results['nicmac1'] = "%02X:%02X:%02X:%02X:%02X:%02X" % (ord(smbios_data[6]), ord(smbios_data[7]), ord(smbios_data[8]), ord(smbios_data[9]), ord(smbios_data[10]), ord(smbios_data[11]))
				results['nicmac2'] = "%02X:%02X:%02X:%02X:%02X:%02X" % (ord(smbios_data[14]), ord(smbios_data[15]), ord(smbios_data[16]), ord(smbios_data[17]), ord(smbios_data[18]), ord(smbios_data[19]))
				

		in_network_settings = False
		for line in data:
			if not in_network_settings and not '<GET_NETWORK_SETTINGS>' in line: continue
			if '<GET_NETWORK_SETTINGS>' in line:
				in_network_settings = True
				continue
			if '</GET_NETWORK_SETTINGS>' in line:
				in_network_settings = False
				continue
			if in_network_settings and '<MAC_ADDRESS' in line:
				value = line.split("VALUE=\"")[1].split("\"")[0]
				results['oobmac'] = value.upper()

		in_power_supplies = False
		this_power_supply = ''
		results['rpsused'] = 0
		for line in data:
			if not in_power_supplies and not '<POWER_SUPPLIES>' in line: continue
			if '<POWER_SUPPLIES>' in line:
				in_power_supplies = True
				continue
			if '</POWER_SUPPLIES>' in line:
				in_power_supplies = False
				continue
			if in_power_supplies:
				if '<SUPPLY>' in line: this_power_supply = ''
				if this_power_supply == None:
					pass
				elif this_power_supply == '':
					if '<LABEL' in line: this_power_supply = line.split("Power Supply ")[1].split("\"")[0]
				elif len(this_power_supply) > 0:
					if '<STATUS' in line:
						value = line.split("VALUE = \"")[1].split("\"")[0]
						if value == "Ok": results['rpsused'] = results['rpsused'] + 1
				if '</SUPPLY' in line: this_power_supply = None
		return results

	def from_smbios_string(self, name, smbios_data, strings, length, offset, this):
		tmp = ''
		if length >= offset:
			stringid = ord(smbios_data[offset])
			if stringid > 0 and len(strings) >= stringid:
				tmp = strings[stringid-1].strip()
		if tmp != '':
			this[name] = tmp

def main():
	gen = None

	cat = catlib.Category(wikipedia.getSite(), 'Category:HP ILO2')
	hosts_gen = pagegenerators.CategorizedPageGenerator(cat, start = None, recurse = False)
	hosts_gen = pagegenerators.PreloadingGenerator(hosts_gen)

	bot = ILO2InventoryBot(hosts_gen) 
	bot.run()

if __name__ == "__main__":
	try:
		main()
	finally:
		wikipedia.stopme()

