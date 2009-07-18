#!/usr/bin/python
# -*- coding: utf-8  -*-
"""

"""
import wikipedia
import pagegenerators, catlib, re, socket, sys
import base64
import struct

class ILO2ImportBot:

	def __init__(self, name, ip):
		self.name = name
		self.ip = ip

	def run(self):
		wikipedia.setAction(u'Robot: hardware import')
		page = wikipedia.Page(wikipedia.getSite(), self.name)
		tmpl = """{{MODEL|
|NAME=
|LOCATION=
|OWNER=
|SN=
|PN=
|OOBIP=
|OOBMAC=
|RPSUSED=1
|NICUSED=2
|NIC1=eth0
|NIC2=eth1
|NICMAC1=
|NICMAC2=
|CPUUSED=2x UnknownCPU
|RAMUSED=2x UnknownMB
|DISKSUSED=2x 146GB
|CONTRACT=
}}
{{Instance
|USAGE=[[OpenVZ HN]]
|OS=lenny
|ARCH=x86_64
|AUTH=ldap
|LDAPGROUP=hostgroup-admin-ssh
|ETH=
}}
"""

		lines = list()
		oldlines = tmpl.split("\n")

		data = self.fetchIloData(self.ip)
		print data

		# now replace the values
		for line in oldlines:
			if line.startswith("{{MODEL"): line = "{{HP_" + data['productname'].replace('ProLiant','').replace(' ','_') + '|'
			if line.startswith("|NAME"): line = "|NAME=" + self.name
			if line.startswith("|OOBIP"): line = "|OOBIP=" + self.ip
			if line.startswith("|LOCATION"): line = "|LOCATION=" + ('%s-%s' % (self.name.split('-')[0], self.name.split('-')[1]))
			if line.startswith("|SN=") and data.has_key('serialnumber'):
				line = "|SN=" + data['serialnumber']
				del data['serialnumber']
			if line.startswith("|PN=") and data.has_key('skunumber'):
				line = "|PN=" + data['skunumber']
				del data['skunumber']
			if line.startswith("|OOBMAC") and data.has_key('oobmac'):
				line = "|OOBMAC=" + data['oobmac']
				del data['oobmac']
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
				# hardware template is over, ensure that no other changes are made
				data = dict()
			lines.append(line)
		pagetext = "\r\n".join(lines)

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

		# now process data
		data = data.split("\n")

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
				# CPU ID
				length = ord(smbios_data[0x1])
				strings = smbios_data[length:].split("\x00")
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

	bot = ILO2ImportBot(sys.argv[1], sys.argv[2]) 
	bot.run()

if __name__ == "__main__":
	try:
		main()
	finally:
		wikipedia.stopme()

