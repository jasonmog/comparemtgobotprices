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
			
			response = response.read().decode('utf-8', 'ignore')
			
			priceList.load(response)
		
	def comparePriceLists(self):
		for i in range(0, len(self.priceLists)):
			a = self.priceLists[i]
			
			for j in range(i + 1, len(self.priceLists)):
				b = self.priceLists[j]
				
				print('Comparing ' + a.url + ' (A) and ' + b.url + ' (B)')

				comparison = a.compareTo(b)
				
				for cardComparison in comparison.aSellingLessThanB:
					sell = cardComparison.sellCard.sellPrice
					buy = cardComparison.buyCard.buyPrice
					profit = buy - sell
					
					if (profit < .1 or profit > 2):
						continue
					
					msg = cardComparison.buyCard.name + ':\nSELL ' + str(sell) + ' (A)'
					msg += ' BUY ' + str(buy) + ' (B) = ' + str(profit) + '\n\n'
					
					print(msg)

				for cardComparison in comparison.bSellingLessThanA:
					sell = cardComparison.sellCard.sellPrice
					buy = cardComparison.buyCard.buyPrice
					profit = buy - sell
					
					if (profit < .1 or profit > 2):
						continue
					
					msg = cardComparison.buyCard.name + ':\nSELL ' + str(sell) + ' (B)'
					msg += ' BUY ' + str(buy) + ' (A) = ' + str(profit) + '\n\n'
					
					print(msg)
					
class PriceList:
	def __init__(self, url):
		self.cards = {}
		self.url = url
		
	def load (self, response):
		singlePricePattern = re.compile(r"([A-Z][a-z][a-zA-Z-',\/]+( [a-zA-Z-',\/]+)*).+?([0-9]+[0-9\.]*)")
		doublePricePattern = re.compile(r"([A-Z][a-z][a-zA-Z-',\/]+( [a-zA-Z-',\/]+)*).+?([0-9]+[0-9\.]*) +([0-9]+[0-9\.]*)")
		
		for line in response.splitlines():
			print('Parsing: ' + line)
			
			match = doublePricePattern.search(line)
			
			if match is None:
				match = singlePricePattern.search(line)
		
				if match is None:
					continue
					
			groups = match.groups()
				
			if (len(groups) >= 4):
				buy = float(groups[2])
				sell = float(groups[3])
			else:
				buy = None
				sell = float(groups[2])
				
			name = groups[0].strip()
				
			card = Card(name, buy, sell, line)
			
			if sell is None:
				sell = ''
			else:
				sell = str(sell)
			
			print('Loaded ' + card.name + ' ' + str(card.buyPrice) + '/' + sell)
				
			if self.cards.get(name) is not None:
				continue
				
			self.cards[name] = card
				
	def compareTo (self, priceList):
		result = PriceListComparison(self, priceList)
		
		aSellingLessThanB = []
		bSellingLessThanA = []
		
		for name in self.cards:
			a = self.get(name)
			b = priceList.get(name)
			
			if b is None:
				continue
				
			if a.buyPrice is not None and b.sellPrice is not None:
				if a.buyPrice > b.sellPrice:
					bSellingLessThanA.append(CardComparison(a, b))
				
			if b.buyPrice is not None and a.sellPrice is not None:
				if b.buyPrice > a.sellPrice:
					aSellingLessThanB.append(CardComparison(b, a))
				
		result.aSellingLessThanB = aSellingLessThanB
		result.bSellingLessThanA = bSellingLessThanA
		
		return result
		
	def get (self, name):
		return self.cards.get(name)
		
class Card:
	def __init__(self, name, buyPrice, sellPrice, line):
		self.name = name
		self.buyPrice = buyPrice
		self.sellPrice = sellPrice
		self.line = line
		
class PriceListComparison:
	def __init__(self, a, b):
		self.priceListA = a
		self.priceListB = b
		self.aSellingLessThanB = []
		self.bSellingLessThanA = []
		
class CardComparison:
	def __init__(self, buy, sell):
		self.buyCard = buy
		self.sellCard = sell
		
compare = CompareMTGOBotPrices()
compare.start()