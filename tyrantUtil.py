import argparse
from collections import Counter
import math
#import numpy
from operator import itemgetter
import os
import random
import re
import resultsDatabase
import subprocess
import xml.sax

import deckBuilder
import deckHasher
import deckOutput
import cardLoader
import simulator
import tyrantArgs

def runStep(step, versus, args, resultsDb, replacementSets, ownedCards, commanderIds, playedIds, uniqueIds, legendaryIds):
    print("Starting step " + str(step))

    sortInDeckHash = not(args.ordered == 1)

    replacementOffset = step % len(replacementSets)
    print("\t... replacementOffset: " + str(replacementOffset))

    deckHashes = []
    if step == 0:
        for deck_i in range(0, 1):
            randomDeck = deckBuilder.randomDeck(commanderIds, playedIds, legendaryIds, uniqueIds)
            deckHashes.append(deckHasher.deckToHash(randomDeck, sortInDeckHash))

        if("hash" in versus and len(versus["hash"]) > 0):
            if(args.defense):
                attackHashes = versus["hash"]
                defenseHashes = deckHashes
            else:
                attackHashes = deckHashes
                defenseHashes = versus["hash"]
            resultsDb = simulator.runSimulationMatrix(attackHashes, defenseHashes, args.numSims, resultsDb)
            resultScores = simulator.getAttackScores(resultsDb, defenseHashes, attackHashes, args.defense)

        if("mission" in versus and len(versus["mission"]) > 0):
            #TODO all this key conversion stuff should get rolled into getAttackScores...
            missionId = versus["mission"][0]
            missionKey = resultsDatabase.deckKey("mission", missionId)
            #print("found a mission: " + missionKey)
            resultsDb = simulator.runMissionGroup(deckHashes, missionId, args.numSims, args.ordered, args.surge, resultsDb)
            resultScores = simulator.getAttackScores(resultsDb, [missionKey], deckHashes, False)

    else:
        previousFile = args.outputDir + args.prefix + str(step - 1) + ".txt"
        previousHashes = cardLoader.loadHashesFromFile(previousFile, 1)

        for evolve_i in range(0, 11):
            if((evolve_i == 0) and args.ignoreCommanders):
                continue

            print("\t... index " + str(evolve_i))
            intermediateSteps = []

            for oldHash_i in range(0, len(previousHashes)):
                evolvedHash = previousHashes[oldHash_i]
                print("\t... evolving deck " + str(oldHash_i) + ": " + evolvedHash)

                evolvedDeck = deckHasher.hashToDeck(evolvedHash)
                evolvedDecks = []

                replacements = commanderIds
                if(evolve_i > 0):
                    replacementIndex = (evolve_i - 1 + replacementOffset) % len(replacementSets)
                    replacements = deckBuilder.updateReplacementsForIndex(set(replacementSets[replacementIndex]), evolvedDeck, evolve_i, uniqueIds, legendaryIds, ownedCards)

                evolvedDecks.extend(deckBuilder.deckEvolutionsForIndex(evolvedDeck, evolve_i, replacements))
                if(args.ordered and evolve_i > 0):
                    swap_index = (evolve_i + step) % 10 + 1
                    evolvedDecks.extend(deckBuilder.orderSwap(evolvedDeck, evolve_i, range(swap_index, swap_index + 1)))

                evolvedHashes = [deckHasher.deckToHash(deck, sortInDeckHash) for deck in evolvedDecks]
                evolvedHashes.append(evolvedHash) # keep refining the one at the top to keep it honest

                resultScores = simulator.runVersusMatrix(versus, evolvedHashes, resultsDb, args.numSims, args.defense, args.ordered, args.surge)

                previousHashes[oldHash_i] = resultScores[0][0]
                intermediateSteps.append(resultScores[0])

            print(deckOutput.outputStringFromResults(intermediateSteps))

        deckHashes = list(previousHashes)

    resultScores = simulator.getVersusScores(resultsDb, evolvedHashes, versus, args.defense)
    if(len(resultScores) > 20):
        resultScores = resultScores[0:20]
    deckOutput.saveStep(args.outputDir, args.prefix, str(step), resultScores)

def main():
    args = tyrantArgs.getArgs()
    cards = cardLoader.loadCardsWithArgs(args)
    
    ownedCards = []
    ownedCardsSet = set()
    if(args.owned):
        ownedCards = cardLoader.loadCardsFromNameFile(args.ownedFile, cards)
        ownedCardsSet = set(ownedCards.elements())

    [commanderIds, playedIds, uniqueIds, legendaryIds] = cardLoader.getIdsFromCardData(cards, ownedCardsSet, args.ignoreActions, args.ignoreCommons)

    numberOfPlayedCards = 10
    replacementSets = deckBuilder.createReplacementSets(playedIds, numberOfPlayedCards)

    ###args line

    tyrantArgs.processPrefix(args)
    versus = tyrantArgs.getVersus(args)

    resultsDb = {}
    stepsRemaining = args.stepCount
    step = -1
    while(stepsRemaining > 0):
        step = step + 1

        stepFile = args.outputDir + args.prefix + str(step) + ".txt"
        if(os.path.exists(stepFile)):
            print("Step " + str(step) + " file found. Skipping...")
            continue

        runStep(step, versus, args, resultsDb, replacementSets, ownedCards, commanderIds, playedIds, uniqueIds, legendaryIds)
        stepsRemaining = stepsRemaining - 1

    #print(len(resultsDb['m_347'].keys()))

main()