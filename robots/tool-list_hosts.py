#!/usr/bin/python
# -*- coding: utf-8  -*-
"""

"""
import wikipedia
import pagegenerators, catlib, re, socket, sys

class IpNetworkBot:

	def __init__(self, hosts_generator):
		self.hosts_generator = hosts_generator

	def run(self):
		for page in self.hosts_generator:
			if ":" in page.title(): continue
			print page.title()

def main():
	gen = None

	cat = catlib.Category(wikipedia.getSite(), 'Category:Debian')
	hosts_gen = pagegenerators.CategorizedPageGenerator(cat, start = None, recurse = False)
	hosts_gen = pagegenerators.PreloadingGenerator(hosts_gen)

	bot = IpNetworkBot(hosts_gen) 
	bot.run()

if __name__ == "__main__":
	try:
		main()
	finally:
		wikipedia.stopme()
