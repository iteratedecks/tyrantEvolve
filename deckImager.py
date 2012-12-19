#!/Applications/Python/python.exe
import argparse
import deckHasher

argParser = argparse.ArgumentParser(description='Output a basic HTML page with links to Fansite decks')
argParser.add_argument('-c', '--cardsFile', default='cards.xml', help='file containing card xml data')
argParser.add_argument('-d', '--dataDir', default='evolution/data/', help='directory holding the deck data')
argParser.add_argument('-l', '--linkPrefix', default='http://tyrant.40in.net/kg/deck.php?nid=', help='URL prefix')
argParser.add_argument('-p', '--dataPrefix', default='evolution', help='prefix for files to parse')
argParser.add_argument('startStep', type=int, default=0, help='start from this evolution step')
argParser.add_argument('endStep', type=int, default=2, help='end at this evolution step (exclusive)')

args = argParser.parse_args()

cardsFile = args.cardsFile
filePrefex = args.dataPrefix
linkPrefex = args.linkPrefix
dataDirectory = args.dataDir + filePrefex + "/"
evolutionStart = args.startStep
evolutionEnd = args.endStep
evolutions = []
'''
for step in range(evolutionStart, evolutionEnd):
    stepStart = str(step)
    previousFile = dataDirectory + filePrefex + stepStart + ".txt"
'''
for step in range(0,1):
    previousFile = "evolution/data/factions/Blue_Note20121012.txt"
    try:
        f = open(previousFile, 'r')
    except IOError as e:
        continue
    hashesFound = -1 # we are 0 indexed
    for line in f:
        line = line.strip()
        if(len(line) == 0 or line[0] == "#"): continue

        previousHash = line.split('\t')[0]
        hashesFound += 1
        if(step == evolutionStart):
            evolutions.append([previousHash])
        else:
            evolutions[hashesFound].append(previousHash)
    f.close()

print("<html><body>")
for evolution in evolutions:
    for deck in evolution:
        print("<a href='" + linkPrefex + deck + "'>" + deck + "</a>")
        print("<!-- ")
        print(deckHasher.hashToDeck(deck))
        print("-->")
        print("<br/>")
    print("<br/>")
print("</body></html>")