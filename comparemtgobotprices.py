import fileinput
import urllib.request
import re
import urllib.parse
import queue
import threading
import urllib.error

class CompareMTGOBotPrices:
	def __init__(self):
		self.priceLists = []
		
	def start(self):
		self.loadSets()
		self.loadPriceLists()
		self.populatePriceLists()
		self.comparePriceLists()
		
	def loadSets(self):
		self.sets = []
		
		for code in fileinput.input('sets.txt'):
			self.sets.append(code.strip())
		
	def loadPriceLists(self):
		for url in fileinput.input('pricelists.txt'):
			url = url.strip()
			
			print('Loading file: ' + url)
			
			self.priceLists.append(PriceList(url))
			
	def populatePriceLists(self):
		q = queue.Queue()
		
		def populatePriceList(priceList):
			print('Requesting URL: ' + priceList.url)

			try:
				response = urllib.request.urlopen(priceList.url)

				response = response.read().decode('utf-8', 'ignore')

				priceList.load(response, self.sets)
				
				return True
			except urllib.error.HTTPError:
				return False
		
		def processPriceListQueue (q):
			while True:
				populatePriceList(q.get())
				q.task_done()
			
		for i in range(8):
			worker = threading.Thread(target=processPriceListQueue, args=(q,))
			worker.setDaemon(True)
			worker.start()
		
		for priceList in self.priceLists:
			q.put(priceList)
			
		q.join()
		
	def comparePriceLists(self):
		for i in range(0, len(self.priceLists)):
			a = self.priceLists[i]
			
			aURL = urllib.parse.urlparse(a.url)
			
			for j in range(i + 1, len(self.priceLists)):
				b = self.priceLists[j]

				bURL = urllib.parse.urlparse(b.url)
				
				if aURL.netloc == bURL.netloc:
					continue
				
				print('Comparing ' + a.url + ' (A) and ' + b.url + ' (B)')

				comparison = a.compareTo(b)
				
				for cardComparison in comparison.aSellingLessThanB:
					sell = cardComparison.sellCard.sellPrice
					buy = cardComparison.buyCard.buyPrice
					
					if (cardComparison.profit < .25 or cardComparison.profit > 2):
						continue
					
					msg = cardComparison.buyCard.name + ':\nSELL ' + str(sell) + ' (A)'
					msg += ' BUY ' + str(buy) + ' (B) = ' + str(cardComparison.profit) + '\n'
					msg += cardComparison.sellCard.line + '\n'
					msg += cardComparison.buyCard.line + '\n\n'
					
					print(msg)

				for cardComparison in comparison.bSellingLessThanA:
					sell = cardComparison.sellCard.sellPrice
					buy = cardComparison.buyCard.buyPrice
					
					if (cardComparison.profit < .25 or cardComparison.profit > 2):
						continue
					
					msg = cardComparison.buyCard.name + ':\nSELL ' + str(sell) + ' (B)'
					msg += ' BUY ' + str(buy) + ' (A) = ' + str(cardComparison.profit) + '\n'
					msg += cardComparison.sellCard.line + '\n'
					msg += cardComparison.buyCard.line + '\n\n'
					
					print(msg)
					
class PriceList:
	def __init__(self, url):
		self.cards = []
		self.url = url
		
	def load (self, response, sets):
		#singlePricePattern = re.compile(r"([A-Z][a-z][a-zA-Z-',\/]+( [a-zA-Z-',\/0-9]+)*\*?).+?\b([0-9]+[0-9\.]*)")
		doublePricePattern = re.compile(r"([A-Z][a-z][a-zA-Z-',\/]+( [a-zA-Z-',\/0-9]+)*\*?).+?\b([0-9]+[0-9\.]*) +([0-9]+[0-9\.]*)")
		setsPattern = re.compile('\\b' + '|'.join(sets) + '\\b')
		
		for line in response.splitlines():
			#print('Parsing: ' + line)
			
			match = doublePricePattern.search(line)
			
			if match is None:
				continue # skip cards with only buy or sell price. can't tell if the price is buy or sell
				match = singlePricePattern.search(line)
		
				if match is None:
					continue
					
			setMatch = setsPattern.search(line)
			
			if setMatch is None:
				continue
					
			groups = match.groups()
				
			if (len(groups) >= 4):
				buy = float(groups[2])
				sell = float(groups[3])
			else:
				buy = None
				sell = float(groups[2])
				
			name = groups[0].strip()
			
			setCode = setMatch.group(0)
			
			if name.endswith('*'):
				foil = True
				
				name = name[0:len(name) - 1]
			else:
				if name.startswith('Foil '):
					foil = True
				
					name = name[len('Foil '):len(name)]
				else:
					foil = False
				
			card = Card(name, setCode, foil, buy, sell, line)
			
			if sell is None:
				sell = ''
			else:
				sell = str(sell)
			
			#print('Loaded: ' + str(card))
				
			self.cards.append(card)
				
	def compareTo (self, priceList):
		result = PriceListComparison(self, priceList)
		
		aSellingLessThanB = []
		bSellingLessThanA = []
		
		for a in self.cards:
			b = priceList.get(a)
			
			if b is None:
				continue
				
			if a.buyPrice is not None and b.sellPrice is not None:
				if a.buyPrice > b.sellPrice:
					bSellingLessThanA.append(CardComparison(a, b))
				
			if b.buyPrice is not None and a.sellPrice is not None:
				if b.buyPrice > a.sellPrice:
					aSellingLessThanB.append(CardComparison(b, a))
				
		result.aSellingLessThanB = sorted(aSellingLessThanB, key=lambda x: x.profit, reverse=True)
		result.bSellingLessThanA = sorted(bSellingLessThanA, key=lambda x: x.profit, reverse=True)
		
		return result
		
	def get (self, needle):
		for card in self.cards:
			if card.name == needle.name and card.foil == needle.foil and card.setCode == needle.setCode:
				return card
				
		return None
		
class Card:
	def __init__(self, name, setCode, foil, buyPrice, sellPrice, line):
		self.name = name
		self.buyPrice = buyPrice
		self.sellPrice = sellPrice
		self.line = line
		self.setCode = setCode
		self.foil = foil
		
	def __str__(self):
		return str({ 'name': self.name, 'setCode': self.setCode, 'foil': self.foil, 'buy': str(self.buyPrice), 'sell': str(self.sellPrice)})
		
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
		self.profit = buy.buyPrice - sell.sellPrice
		
compare = CompareMTGOBotPrices()
compare.start()