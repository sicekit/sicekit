#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This bot regenerates all IP-Network pages

The following parameters are supported:

    -debug         If given, doesn't do any real changes, but only shows
                   what would have been changed.

"""
__version__ = '$Id: basic.py 4946 2008-01-29 14:58:25Z wikipedian $'
import wikipedia
import pagegenerators, catlib, re, socket, sys
from iplib import CIDR, IPv4Address

class IPv4Host:
  def __init__(self, ip, name, is_host=True, is_vip=False, type=None):
    self.ip = IPv4Address(ip)
    self.name = name
    self.is_vip = is_vip
    self.is_host = is_host
    self.type = type

  def __cmp__(self, other):
    return cmp(self.ip, other.ip)

class IpNetworkBot:
    # Edit summary message that should be used.
    # NOTE: Put a good description here, and add translations, if possible!
    msg = {
        'en': u'Robot: regenerated network pages.',
    }

    def __init__(self, nets_generator, hosts_generator, debug):
        """
        Constructor. Parameters:
            * generator - The page generator that determines on which pages
                          to work on.
            * debug     - If True, doesn't do any real changes, but only shows
                          what would have been changed.
        """
        self.nets_generator = nets_generator
        self.hosts_generator = hosts_generator
        self.nets = dict()
        self.debug = debug

    def registerIpNet(self, page):
        if ":" in page.title(): return
        text = page.get()
        defaultgw = None
        router = None
        cidr = CIDR(page.title())
        iplist = dict()

        if cidr.broadcast_ip:
          # protect against /32 networks
          iplist[str(cidr.broadcast_ip)] = IPv4Host(cidr.broadcast_ip, 'Broadcast', is_vip=True, is_host=False)
          iplist[str(cidr.network_ip)] = IPv4Host(cidr.network_ip, 'Begin of Network', is_vip=True, is_host=False)

        for line in text.split("\n"):
          if line.startswith("|DEFAULTGW="):
            defaultgw = IPv4Address(line.split('=')[1])
          if line.startswith("|ROUTER="):
            router = line.split('=')[1].strip()
          if line.startswith("|DHCP="):
            #epic dhcp range
            for range in line.split('=')[1].split(','):
              ipa, ipb = range.strip().split('-')
              iplist[str(IPv4Address(ipa))] = IPv4Host(ipa, 'DHCP-Dynamic Start', is_vip=True, is_host=False)
              iplist[str(IPv4Address(ipb))] = IPv4Host(ipb, 'DHCP-Dynamic End', is_vip=True, is_host=False)

        if defaultgw and router:
          iplist[str(defaultgw)] = IPv4Host(defaultgw, router, is_vip=True, is_host=True)

        self.nets[page.title()] = {"cidr": cidr, "list": iplist, "page": page, "defaultgw": defaultgw, "router": router}

    def findIpNetForIp(self, address):
        for net in self.nets.keys():
          if not self.nets[net]["cidr"].is_valid_ip(address): continue
          return net

    def registerIpAddress(self, address, prefix, type, page):
        if not "lbvlan" in page.title() and not "bordervlan" in page.title(): return
        whatsit = ''
        if "lbvlan" in page.title(): whatsit = 'LB'
        if "bordervlan" in page.title(): whatsit = 'BORDER'
        vlan = page.title().split('vlan', 2)[1].split('.')[0]
        net = self.findIpNetForIp(address)
        print "%- 7s %- 5s %- 15s %- 19s %s" % (whatsit, vlan, address, net, self.nets[net]["cidr"])

    def registerIpHost(self, page):
        if ":" in page.title(): return
        try:
            # Load the page
            text = page.get()
        except wikipedia.NoPage:
            wikipedia.output(u"Page %s does not exist; skipping." % page.aslink())
            return
        except wikipedia.IsRedirectPage:
            wikipedia.output(u"Page %s is a redirect; skipping." % page.aslink())
            return
        ipR = re.compile('(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?:(/\d+)\|(\d+))?')

        wikipedia.output(page.urlname())
        for line in text.split("\n"):
          # only care about ips which are relevant.
          if not (line.startswith("|MGMTIP") or line.startswith("|OOBIP") or line.startswith("|ETH") or line.startswith("|IP") or line.startswith("{{")):
            continue
          # now see all ips.
          for m in ipR.finditer(line):
            if not m: continue
            baseip, netprefix, netip = m.groups()
            if netprefix and netip:
              ip = baseip.rsplit('.', 1)[0] + '.' + netip
            else:
              ip = baseip
            longip = socket.inet_aton(ip)
            type=None
            if line.startswith('|MGMTIP'): type='MGMT'
            if line.startswith('|OOB'): type='OOB'
            self.registerIpAddress(ip, netprefix, type, page)

    def run(self):
        for page in self.nets_generator:
            self.registerIpNet(page)

        for page in self.hosts_generator:
            self.registerIpHost(page)


def main():
    # The generator gives the pages that should be worked upon.
    gen = None
    # If debug is True, doesn't do any real changes, but only show
    # what would have been changed.
    debug = False
    wantHelp = False


    # Parse command line arguments
    for arg in wikipedia.handleArgs():
        if arg.startswith("-debug"):
            debug = True
        else:
            wantHelp = True

    if not wantHelp:
        # The preloading generator is responsible for downloading multiple
        # pages from the wiki simultaneously.

        cat = catlib.Category(wikipedia.getSite(), 'Category:%s' % 'Virtual-IP')
        hosts_gen = pagegenerators.CategorizedPageGenerator(cat, start = None, recurse = False)
        hosts_gen = pagegenerators.PreloadingGenerator(hosts_gen)

        cat = catlib.Category(wikipedia.getSite(), 'Category:%s' % 'IP-Network')
        nets_gen = pagegenerators.CategorizedPageGenerator(cat, start = None, recurse = False)
        nets_gen = pagegenerators.PreloadingGenerator(nets_gen)

        bot = IpNetworkBot(nets_gen, hosts_gen, debug)
        bot.run()
    else:
        wikipedia.showHelp()

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
