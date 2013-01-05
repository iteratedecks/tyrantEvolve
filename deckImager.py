import argparse
import deckHasher

# This regex works to translate Kong image links into BBCode image links
# .*"!([^!]+)!":([^=]+=(.*))$
# [tr][td]\3[/td][td][url=\2][img]\1[/img][/url][/td][/tr]

argParser = argparse.ArgumentParser(description='Output a basic HTML page with links to Fansite decks')
argParser.add_argument('-c', '--cardsFile', default='cards.xml', help='file containing card xml data')
argParser.add_argument('-l', '--linkPrefix', default='http://tyrant.40in.net/kg/deck.php?nid=', help='URL prefix')

argParser.add_argument('file', help='File containing decks to image')

args = argParser.parse_args()

cardsFile = args.cardsFile
linkPrefex = args.linkPrefix
files = [args.file]

evolutions = []
'''
for step in range(evolutionStart, evolutionEnd):
    stepStart = str(step)
    previousFile = dataDirectory + filePrefex + stepStart + ".txt"
'''
for file in files:
    try:
        f = open(file, 'r')
    except IOError as e:
        continue
    for line in f:
        line = line.strip()
        if(len(line) == 0 or line[0] == "#"): continue

        previousHash = line.split('\t')[0]
        evolutions.append([previousHash])
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
