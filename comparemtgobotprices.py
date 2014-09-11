import fileinput
import urllib.request
import re

class CompareMTGOBotPrices:
	def __init__(self):
		self.priceLists = []
		
	def start(self):
		self.loadPriceLists()
		self.populatePriceLists()
		self.comparePriceLists()
		
	def loadPriceLists(self):
		for url in fileinput.input('pricelists.txt'):
			url = url.strip()
			
			print('Loading file: ' + url)
			
			self.priceLists.append(PriceList(url))
			
	def populatePriceLists(self):
		for priceList in self.priceLists:
			print('Requesting URL: ' + priceList.url)
		
			response = urllib.request.urlopen(priceList.url)
			
			str = response.read().decode('utf-8', 'ignore')
			
			priceList.load(str)
		
	def comparePriceLists(self):
		for i in range(0, len(self.priceLists)):
			priceList = self.priceLists[i]
			
			for j in range(i + 1, len(self.priceLists)):
				b = self.priceLists[j]
				
				print('Comparing ' + priceList.url + ' and ' + b.url)

				comparison = priceList.compareTo(b)
				
				for card in comparison.aSellingLessThanB:
					print(card.name + ': SELL ' + card.sellPrice + ' (' + comparison.priceListA.url + ') BUY ' + comparison.priceListB.get(card.name).buyPrice + ' (' + comparison.priceListB.url + ')')

				for card in comparison.bSellingLessThanA:
						print(card.name + ': SELL ' + card.sellPrice + ' (' + comparison.priceListB.url + ') BUY ' + comparison.priceListA.get(card.name).buyPrice + ' (' + comparison.priceListA.url + ')')
					
class PriceList:
	def __init__(self, url):
		self.cards = {}
		self.url = url
		
	def load (self, str):
		singlePricePattern = re.compile(r"([A-Z][a-z][a-zA-Z- ',]+?) [ \[].*([0-9]+\.[0-9]+)")
		doublePricePattern = re.compile(r"([A-Z][a-z][a-zA-Z- ',]+?) [ \[].*([0-9]+\.[0-9]+) +([0-9]+\.[0-9]+)")
		
		for line in str.splitlines():
			match = doublePricePattern.search(line)
			
			if match == None:
				match = singlePricePattern.search(line)
		
				if match == None:
					continue
					
			groups = match.groups()
				
			if (len(groups) >= 3):
				sell = groups[2]
			else:
				sell = None
				
			name = groups[0]
				
			card = Card(name, groups[1], sell)
			
			if sell == None:
				sell = ''
			
			print('Loaded ' + card.name + ' ' + card.buyPrice + '/' + sell)
				
			self.cards[name] = card
				
	def compareTo (self, priceList):
		result = PriceListComparison(self, priceList)
		
		aSellingLessThanB = []
		bSellingLessThanA = []
		
		for name in self.cards:
			a = self.get(name)
			b = priceList.get(name)
			
			if b == None:
				continue
				
			print(name)
				
			if a.buyPrice != None and b.sellPrice != None:
				if a.buyPrice > b.sellPrice:
					print('A Buy: ' + a.buyPrice + ' B Sell: ' + b.sellPrice)

					bSellingLessThanA.append(a)
				
			if b.buyPrice != None and a.sellPrice != None:
				if b.buyPrice > a.sellPrice:
					print('A Sell: ' + a.sellPrice + ' B Buy: ' + b.buyPrice)

					aSellingLessThanB.append(a)
				
		result.aSellingLessThanB = aSellingLessThanB
		result.bSellingLessThanA = bSellingLessThanA
		
		return result
		
	def get (self, name):
		return self.cards.get(name)
		
class Card:
	def __init__(self, name, buyPrice, sellPrice):
		self.name = name
		self.buyPrice = buyPrice
		self.sellPrice = sellPrice
		
class PriceListComparison:
	def __init__(self, a, b):
		self.priceListA = a
		self.priceListB = b
		self.aSellingLessThanB = []
		self.bSellingLessThanA = []
		
compare = CompareMTGOBotPrices()
compare.start()