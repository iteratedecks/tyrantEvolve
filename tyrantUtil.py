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
                    #if(swap_index != evolve_i):
                    #print("swapping " + str(evolve_i) + " for " + str(swap_index))
                    evolvedDecks.extend(deckBuilder.orderSwap(evolvedDeck, evolve_i, range(swap_index, swap_index + 1)))

                evolvedHashes = [deckHasher.deckToHash(deck, sortInDeckHash) for deck in evolvedDecks]
                evolvedHashes.append(evolvedHash) # keep refining the one at the top to keep it honest

                attackKeys = evolvedHashes
                defenseKeys = None
                defenseVersus = versus
                if("hash" in versus and len(versus["hash"]) > 0):
                    if(args.defense):
                        attackKeys = versus["hash"]
                        defenseVersus = { "hash": evolvedHashes }
                    #else:
                    #    attackKeys = evolvedHashes
                    #    defenseVersus = versus
                    #resultsDb = simulator.runSimulationMatrix(attackKeys, defenseHashes, args.numSims, resultsDb)

                if("mission" in versus and len(versus["mission"]) > 0):
                    #TODO all this key conversion stuff should get rolled into getAttackScores...
                    missionId = versus["mission"][0]
                    #print("found a mission: " + str(missionId))
                    missionKey = resultsDatabase.deckKey("mission", missionId)
                    defenseKeys = [missionKey]

                if("raid" in versus and len(versus["raid"]) > 0):
                    raidId = versus["mission"][0]
                    raidKey = resultsDatabase.deckKey("raid", raidId)
                    defenseKeys = [raidKey]

                if("quest" in versus and len(versus["quest"]) > 0):
                    questId = versus["quest"][0]
                    questKey = resultsDatabase.deckKey("quest", questId)
                    defenseKeys = [questKey]

                resultsDb = simulator.runMatrix(attackKeys, defenseVersus, args.numSims, args.ordered, args.surge, resultsDb)

                resultScores = simulator.getAttackScores(resultsDb, defenseKeys, attackKeys, args.defense)
                resultScores = sorted(resultScores, key=itemgetter(1), reverse=True)
                previousHashes[oldHash_i] = resultScores[0][0]
                intermediateSteps.append(resultScores[0])

            print(deckOutput.outputStringFromResults(intermediateSteps))

        deckHashes = list(previousHashes)

    # recalculate the scores against the new best
    resultScores = None
    if("hash" in versus and len(versus["hash"]) > 0):
        if(args.defense):
            resultScores = simulator.getAttackScores(resultsDb, None, versus["hash"], args.defense)
        else:
            resultScores = simulator.getAttackScores(resultsDb, versus["hash"], None, args.defense)

    if("mission" in versus and len(versus["mission"]) > 0):
        missionId = versus["mission"][0]
        missionKey = resultsDatabase.deckKey("mission", missionId)
        resultScores = simulator.getAttackScores(resultsDb, [missionKey], None, False)

    if("raid" in versus and len(versus["raid"]) > 0):
        raidId = versus["raid"][0]
        raidKey = resultsDatabase.deckKey("raid", raidId)
        resultScores = simulator.getAttackScores(resultsDb, [raidKey], None, False)

    if("quest" in versus and len(versus["quest"]) > 0):
        questId = versus["quest"][0]
        questKey = resultsDatabase.deckKey("quest", questId)
        resultScores = simulator.getAttackScores(resultsDb, [questKey], None, False)

    resultScores = sorted(resultScores, key=itemgetter(1), reverse=True)
    if(len(resultScores) > 20):
        resultScores = resultScores[0:20]
    deckOutput.saveStep(args.outputDir, args.prefix, str(step), resultScores)

def main():
    #TODO turn the common filter into a flag    
    argParser = argparse.ArgumentParser(description='Run a series of deck simulations.')
    argParser.add_argument('-c', '--ignoreCommanders', default=0, help='skip over commander index')
    argParser.add_argument('-d', '--numDecks', type=int, default=10, help='number of decks to evolve')
    argParser.add_argument('-D', '--defense', type=int, default=0, help='start on defense (1) or offense (0)')
    argParser.add_argument('-m', '--missionId', type=int, help='id of mission to target; note that this is different than "mission 190"')
    argParser.add_argument('-n', '--numSims', type=int, default=100, help='number of simulations per comparison')
    argParser.add_argument('-o', '--ordered', type=int, default=0, help='ordered deck')
    argParser.add_argument('-O', '--owned', type=int, default=0, help='use owned cards as a filter')
    argParser.add_argument('-p', '--prefix', default='default', help='name for evolution set')
    argParser.add_argument('-Q', '--questId', type=int, help='id of quest to target; note that this typically matches Quest Step')
    argParser.add_argument('-r', '--raidId', type=int, help='id of raid to target')
    argParser.add_argument('-s', '--surge', type=int, default=0, help='attack deck surges')
    argParser.add_argument('--cardsFile', default='cards.xml', help='file containing card xml data')
    argParser.add_argument('--defenseFile', help='file containing defense decks')
    argParser.add_argument('--ignoreActions', type=int, default=0, help='Do not use action cards')
    argParser.add_argument('--ignoreCommons', type=int, default=0, help='Do not use commons')
    argParser.add_argument('--outputDir', default='evolution/data/', help='directory to store results')
    argParser.add_argument('--ownedFile', default='wildcard/ownedcards.txt', help='file containing owned cardlist')
    #argParser.add_argument('--startStep', type=int, default=0, help='start from this evolution step')
    argParser.add_argument('stepCount', type=int, default=2, help='end at this evolution step (exclusive)')

    args = argParser.parse_args()
    
    #startStep = args.startStep
    #endStep = args.stepCount + startStep + 1

    cards = cardLoader.loadCardsWithArgs(args)
    
    ownedCards = []
    ownedCardsSet = set()
    if(args.owned):
        ownedCards = cardLoader.loadCardsFromNameFile(args.ownedFile, cards)
        ownedCardsSet = set(ownedCards.elements())

    [commanderIds, playedIds, uniqueIds, legendaryIds] = cardLoader.getIdsFromCardData(cards, ownedCardsSet, args.ignoreActions, args.ignoreCommons)

    numberOfPlayedCards = 10
    replacementSets = deckBuilder.createReplacementSets(playedIds, numberOfPlayedCards)

    #args line

    if(args.prefix == 'default'):
        if(args.missionId != None):
            args.prefix = "mission%02d" % args.missionId
        elif(args.raidId != None):
            args.prefix = "raid%02d" % args.raidId
        #elif(args.questId != None):
        #    filePrefix = "quest%02d" % args.questId

        if(args.ordered):
            args.prefix += "o"
        if(args.surge):
            args.prefix += "s"

    if(args.missionId != None):
        args.outputDir += "missions/"
    elif(args.raidId != None):
        args.outputDir += "raids/"
    elif(args.questId != None):
        args.outputDir += "quests/"

    args.outputDir += args.prefix + "/" #TODO verify directory exists
    
    args.prefix += "_"

    print("using prefix: " + args.prefix)

    versus = {}

    if(args.defenseFile != None):
        versus["hash"] = cardLoader.loadHashesFromFile(args.defenseFile)

    if(args.missionId != None):
        versus["mission"] = [args.missionId]

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