#!/Applications/Python/python.exe
import xml.sax.handler
from collections import namedtuple
from collections import Counter

CardData = namedtuple("CardData", ['id', 'name', 'rarity', 'unique', 'base_card'])

class CardHandler(xml.sax.handler.ContentHandler):
  def __init__(self):
    self.inUnit = 0
    self.inSubelement = 0
    self.ids = []
    self.cards = []
    self.subs = {}
 
  def startElement(self, element, attributes):
    #print(element + " v. ")
    #print(self.subs.keys())
    if element == "unit":
        self.inUnit = 1
        self.subs["rarity"] = "0"
        self.subs["unique"] = "0"
        self.subs["id"] = ""
        self.subs["set"] = ""
        self.subs["name"] = ""
        self.subs["cost"] = "-1"
        self.subs["base_card"] = "0"
    elif (element in self.subs.keys()):
      self.inSubelement = 1
      self.subBuffer = ""

  def characters(self, data):
    if self.inSubelement:
      self.subBuffer += data

  def endElement(self, element):
    if element == "unit":
      self.inUnit = 0
      self.inSubelement = 0 # should not be needed
      # does it exist and have a valid set? (set 9000 is unusable)
      if(self.subs["id"] != "" and self.subs["set"] != "" and self.subs["set"] != "9000"):
        self.ids.append(int(self.subs["id"]))
        self.cards.append(CardData(int(self.subs["id"]),
            self.subs["name"],
            int(self.subs["rarity"]),
            int(self.subs["unique"]),
            int(self.subs["base_card"])))
    elif element in self.subs.keys():
      self.inSubelement = 0
      self.subs[element] = self.subBuffer

def loadCardDataFromXmlFile(file):
    cardParser = xml.sax.make_parser()
    handler = idScanner.CardHandler()
    cardParser.setContentHandler(handler)
    cardParser.parse(file)
    return handler.cards

def loadHashesFromFile(file, top = -1):
    max = 0.0    
    hashes = []
    data = []
    f = open(file, 'r')
    for line in f:
        line = line.strip()
        if(len(line) == 0 or line[0] == "#"): continue

        data.append(line.split('\t'))
    f.close()

    if(top > 0):
        from operator import itemgetter
        data = sorted(data, key=itemgetter(1), reverse=True)
        data = data[:top]

    hashes = [line[0] for line in data]
    #print(hashes)
    return hashes

def loadCardsFromNameFile(file, cardData):
    cardCounts = Counter()
    f = open(file, 'r')
    for line in f:
        line = line.strip()
        if(len(line) == 0 or line[0] == "#"): continue
        name, count = line.split('(')
        count = count.strip(')')
        cardCounts[name] = int(count)
        #print("found '" + name + "'\twith count " + count)
        #names.append(name) #TODO support card counts as well
    f.close()

    idCounts = [[card.id, cardCounts[card.name]] for card in cardData if (cardCounts[card.name] > 0 and card.base_card == 0)]
    counts = Counter(dict(idCounts))
    return counts

def loadCardsWithArgs(args):
    cardsFile = args.cardsFile

    #TODO turn the common filter into a flag    
    
    cardParser = xml.sax.make_parser()
    handler = CardHandler()
    cardParser.setContentHandler(handler)
    cardParser.parse(cardsFile)
    cards = handler.cards

    return cards

def getIdsFromCardData(cardData, filter = [], ignoreActions = True, ignoreCommons = True):
    baseCardData = [card for card in cardData if card.base_card == 0]

    cardIds = set([card.id for card in baseCardData])
    legendaryIds = set([card.id for card in baseCardData if card.rarity == 4])
    uniqueIds = set([card.id for card in baseCardData if card.unique != 0])

    if(len(filter) > 0):
        cardIds = cardIds & filter

    commanderIds = set([id for id in cardIds if (id >= 1000 and id < 2000)])

    # ignore commons for assault and structure cards
    if(ignoreCommons):
        commonIds = set([card.id for card in baseCardData if card.rarity == 1])
        cardIds = cardIds - commonIds

    assaultIds = set([id for id in cardIds if id < 1000])
    structureIds = set([id for id in cardIds if (id >= 2000 and id < 3000)])
    playedIds = assaultIds | structureIds
    
    if(not ignoreActions):
        actionIds = set([id for id in cardIds if (id >= 3000)])
        playedIds = playedIds | actionIds
    
    return [commanderIds, playedIds, uniqueIds, legendaryIds]
