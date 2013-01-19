import math
from collections import namedtuple
import random

CardLists = namedtuple("CardLists", ['commanders', 'played', 'legendaries', 'uniques'])

def randomDeck(commanders, cards, legendaries, uniques):
    #commanders = cardLists.commanders
    #cards = cardLists.played
    #legendaries = cardLists.legendaries
    #uniques = cardLists.uniques

    randomDeck = []
    randomDeck.append(random.sample(commanders,1)[0]) #random.choice does not support sets

    #TODO find out if it is quicker to sample(s, 10) and then replace invalid cards
    for i in range(0, 10):
        newId = random.sample(cards, 1)[0] #random.choice does not support sets
        if(newId in legendaries): # if the card is legendary, we cannot choose any other legendaries
            cards = cards - legendaries

        # if the card is unique, prevent it from being added again
        # also check if the legendary removal already removed it
        if(newId in uniques and newId in cards):
            cards.remove(newId)
        randomDeck.append(newId)

    #randomHash = deckHasher.convertIdListToHashString(randomDeck)
    #print(randomHash + "\t" + str(randomDeck).strip('[]'))
    return randomDeck

def orderSwap(oldDeck, index, targetRange = None):
    if(targetRange is None):
        targetRange = range(1, len(oldDeck))
    newDecks = []
    for old_i in targetRange:
        if(old_i == index):
            continue
        if(oldDeck[old_i] == oldDeck[index]): # skip if they already match
            continue
        newDeck = list(oldDeck)
        newDeck[old_i] = oldDeck[index]
        newDeck[index] = oldDeck[old_i]
        newDecks.append(newDeck)

    return newDecks

#def deckEvolutions(oldDeck, targetIndexes, cardsToUse):
def deckEvolutions(oldDeck, cardLists):
    commanders = cardLists.commanders
    cards = cardLists.played
    legendaries = cardLists.legendaries
    uniques = cardLists.uniques

    targetIndexes = range(0, len(oldDeck))
    #newDecks = deckEvolutionsInRange(oldDeck, [0], commanders, [])
    return deckEvolutionsInRange(oldDeck, targetIndexes, commanders, cards, unqiues, legendaries)    

def deckEvolutionsWithFilter(oldDeck, cardLists, cardFilter):
    commanders = cardLists.commanders
    cards = cardLists.played
    legendaries = cardLists.legendaries
    uniques = cardLists.uniques

    if(len(cardFilter) > 0):
        cards = cards & cardFilter
        commanders = commanders & cardFilter

    targetIndexes = range(0, len(oldDeck))
    return deckEvolutionsInRange(oldDeck, targetIndexes, commanders, cards, unqiues, legendaries)    
    
def deckEvolutionsForIndex(oldDeck, index, replacementSet):
    newDecks = []
    for card in replacementSet:
        newDeck = list(oldDeck)
        newDeck[index] = card
        newDecks.append(newDeck)
    return newDecks

def deckEvolutionsInRange(oldDeck, targetIndexes, commanders, cards, uniques, legendaries):
    newDecks = []

    if(0 in targetIndexes):
        newDecks.extend(deckEvolutionsForIndex(oldDeck, 0, commanders))
        targetIndexes.remove(0)

    replacementSets = createReplacementSets(cards, len(oldDeck) - 1)
    for card_i in targetIndexes:
        newDecks.extend(deckEvolutionsWithCards(oldDeck, card_i, replacementSets[card_i - 1], uniques, legendaries))

    return newDecks

#def deckEvolutionsWithCards(oldDeck, index, replacements, uniques, legendaries):    
#    return deckEvolutionsForIndex(oldDeck, index, updateReplacementsForIndex)

def updateReplacementsForIndex(replacements, oldDeck, index, uniques, legendaries, countFilter):
    if(len(countFilter) > 0):
        countFilter.subtract(oldDeck)
        filter = set(countFilter.elements())
        countFilter.update(oldDeck)

        replacements = replacements & filter

    oldCardSet = set(oldDeck)
    replacements = replacements - (uniques & oldCardSet) # ignore already used uniques
    #print("Checking for legendaries...")
    if(len(oldCardSet & legendaries) > 0): # if we already have a legendary, ignore all legendaries
        #print("Legendaries detected...")
        #print(oldCardSet & legendaries)
        
        if(not(oldDeck[index] in legendaries)):
            replacements = replacements - legendaries
            #print("Swapping for a legendary, readding them...")

    return replacements
    
def createReplacementSets(cards, count):
    replacements = set(cards)
    setSize = int(math.floor(len(replacements) / count))
    replacementSets = []
    for set_i in range(0, count - 1):
        newSet = set(random.sample(replacements, setSize))
        replacementSets.append(newSet)
        replacements.difference_update(newSet)
    replacementSets.append(replacements)
    return replacementSets
