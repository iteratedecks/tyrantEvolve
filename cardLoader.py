import xml.sax.handler
from collections import namedtuple
from collections import Counter

CardData = namedtuple("CardData", ['id', 'name', 'health', 'rarity', 'unique', 'base_card'])

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
        self.subs["id"] = ""
        self.subs["name"] = ""
        self.subs["health"] = "0"
        self.subs["cost"] = "-1"
        self.subs["rarity"] = "0"
        self.subs["unique"] = "0"
        self.subs["set"] = ""
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
            int(self.subs["health"]),
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

        id = line[line.find("[") + 1:line.find("]")]
        count = line[line.find("(") + 1:line.find(")")]
        
        cardCounts[int(id)] = int(count)
        #print("found '" + id + "'\twith count " + count)
        #names.append(name) #TODO support card counts as well
    f.close()

    #idCounts = [[card.id, cardCounts[card.name]] for card in cardData if (cardCounts[card.id] > 0 and card.base_card == 0)]
    #counts = Counter(dict(idCounts))
    #return counts
    #print(cardCounts)
    return cardCounts

def loadCardsWithArgs(args):
    cardsFile = args.cardsFile

    #TODO turn the common filter into a flag    
    
    cardParser = xml.sax.make_parser()
    handler = CardHandler()
    cardParser.setContentHandler(handler)
    cardParser.parse(cardsFile)
    cards = handler.cards

    return cards

def getNotBadExceptions():
    exceptions = set()

#Acid Athenor
    exceptions.add(2012)    # Asylum
    exceptions.add(752) #Atelier
    exceptions.add(2032)    #Blood Wall
    exceptions.add(2101)    #Boot Camp
    exceptions.add(1121)    #Daizon
    exceptions.add(769) #Egg Infector
    exceptions.add(2118)    #Enclave Warp Gate
    exceptions.add(2065)    #Fortified Cannons
    exceptions.add(907) #Gene Reader
    exceptions.add(320) #Gruesome Crawler
    exceptions.add(442) #Heli-Duster
    exceptions.add(37)  #Hunter
    exceptions.add(1020)    #Hydraulis
    exceptions.add(238) #Irradiated Infantry
    exceptions.add(720) #Meteor
    exceptions.add(2034)    #Mirror Wall
    exceptions.add(949) #Mizar VIII
    exceptions.add(888) #Nephilim Knight
    exceptions.add(626) #Neverender
    exceptions.add(2070)    #Offshore Platform
    exceptions.add(457) #Outfitted Scow
    exceptions.add(126) #Pathrazer
    exceptions.add(472)    #Patrol Cruiser
    exceptions.add(1154)    #Patriarch
    exceptions.add(783) #Phantasm
#Phaseid
    exceptions.add(30)  #Predator
    exceptions.add(2090)    #Prism
    exceptions.add(444) #Reclamax
    exceptions.add(1035)    #Ryoko
    exceptions.add(452) #Shaded Hollow
    exceptions.add(2100)    #Shrapnel Engine
    exceptions.add(2129)    #Shrine of Hope
    exceptions.add(154) #Speculus
    exceptions.add(261) #Stealthy Niaq
    exceptions.add(534) #Subterfuge
    exceptions.add(500) #Sundering Ogre
    exceptions.add(103) #Tiamat
    exceptions.add(245) #Toxic Cannon
    exceptions.add(865) #Withersnap
    return exceptions

def getIdsFromCardData(cardData, filter = [], ignoreActions = True, ignoreBad = True):
    baseCardData = [card for card in cardData if card.base_card == 0]

    cardIds = set([card.id for card in baseCardData])
    legendaryIds = set([card.id for card in baseCardData if card.rarity == 4])
    uniqueIds = set([card.id for card in baseCardData if card.unique != 0])

    if(len(filter) > 0):
        cardIds = cardIds & filter

    # ignore commons for assault and structure cards
    if(ignoreBad):
        commonIds = set([card.id for card in cardData if card.rarity == 1])
        uncommonIds = set([card.id for card in cardData if card.rarity == 2])
        lowHealthIds = set([card.id for card in cardData if card.health <= 2])

        badIds = commonIds | uncommonIds | lowHealthIds
        notBadIds = getNotBadExceptions()
        badIds = badIds - notBadIds
        cardIds = cardIds - badIds

    commanderIds = set([id for id in cardIds if (id >= 1000 and id < 2000)])
    assaultIds = set([id for id in cardIds if id < 1000])
    structureIds = set([id for id in cardIds if (id >= 2000 and id < 3000)])
    playedIds = assaultIds | structureIds
    
    if(not ignoreActions):
        actionIds = set([id for id in cardIds if (id >= 3000)])
        playedIds = playedIds | actionIds
    
    return [commanderIds, playedIds, uniqueIds, legendaryIds]
