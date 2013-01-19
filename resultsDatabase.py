resultsDb = {}

def recordResults(defenseKey, attackKey, simResults, db = resultsDb):
    if(db is None):
        print("Warning, empty results database used. Reverting to default.")
        db = resultsDb

    if(not defenseKey in db):
        db[defenseKey] = {}
    if(not attackKey in db[defenseKey]):
        db[defenseKey][attackKey] = [int(simResults[1]), int(simResults[0]), int(simResults[2]), int(simResults[3])]
    else:
        db[defenseKey][attackKey][0] += int(simResults[1])
        db[defenseKey][attackKey][1] += int(simResults[0])
        db[defenseKey][attackKey][2] += int(simResults[2])
        db[defenseKey][attackKey][3] += int(simResults[3])

def deckKey(deckType, deckId, ordered = False):
    prefix = ""

    if(ordered):
        prefix = prefix + "o"

    if(deckType == "mission"):
        prefix = prefix + "m"
    elif(deckType == "raid"):
        prefix = prefix + "r"
    elif(deckType == "quest"):
        prefix = prefix + "q"

    if(prefix != ""):
        prefix = prefix + "_"

    return prefix + str(deckId)
