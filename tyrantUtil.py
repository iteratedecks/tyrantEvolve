import argparse
from collections import Counter
import math
import numpy
from operator import itemgetter
import os
import random
import re
import subprocess
import xml.sax

import deckBuilder
import deckHasher
import deckOutput
import cardLoader
import simulator

def runStep(step, args, resultsDb, replacementSets, ownedCards, commanderIds, playedIds, uniqueIds, legendaryIds):
    dataDirectory = args.outputDir + args.dataPrefix + "/" #TODO verify directory exists
    useDefenseFile = args.defenseFile != None
    enemyHashes = []

    sortInDeckHash = not(args.ordered == 1)
    
    if(useDefenseFile):
        enemyHashes = cardLoader.loadHashesFromFile(args.defenseFile)

    print("Starting step " + str(step))
    stepFile = dataDirectory + args.dataPrefix + str(step) + ".txt"
    if(os.path.exists(stepFile)):
        print("\t... Step " + str(step) + " file found. Skipping...")
        return

    replacementOffset = step % len(replacementSets)
    print("\t... replacementOffset: " + str(replacementOffset))

    deckHashes = []
    if step == 0:
        for deck_i in range(0, 1):
            randomDeck = deckBuilder.randomDeck(commanderIds, playedIds, legendaryIds, uniqueIds)
            deckHashes.append(deckHasher.deckToHash(randomDeck, sortInDeckHash))

        if(not useDefenseFile):
            enemyHashes = list(deckHashes)

        if(len(enemyHashes) > 0):
            if(args.defense):
                attackHashes = enemyHashes
                defenseHashes = deckHashes
            else:
                attackHashes = deckHashes
                defenseHashes = enemyHashes
            resultsDb = simulator.runSimulationMatrix(attackHashes, defenseHashes, args.numSims, resultsDb)
            resultScores = simulator.getAttackScores(resultsDb, defenseHashes, attackHashes, args.defense)

    else:
        previousFile = dataDirectory + args.dataPrefix + str(step - 1) + ".txt"
        previousHashes = cardLoader.loadHashesFromFile(previousFile, 1)

        for evolve_i in range(0, 11):
            print("\t... index " + str(evolve_i))
            intermediateSteps = []

            # copy this state so we do not mess with the defenses later
            if(not useDefenseFile):
                enemyHashes = list(previousHashes)

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
                
                evolvedHashes = [deckHasher.deckToHash(deck, sortInDeckHash) for deck in evolvedDecks]

                # do not evolve if we cannot do better than the old deck
                if(evolvedHash not in evolvedHashes):
                    evolvedHashes.append(evolvedHash)

                if(args.defense):
                    attackHashes = enemyHashes
                    defenseHashes = evolvedHashes
                else:
                    attackHashes = evolvedHashes
                    defenseHashes = enemyHashes
                resultsDb = simulator.runSimulationMatrix(attackHashes, defenseHashes, args.numSims, resultsDb)
                resultScores = simulator.getAttackScores(resultsDb, defenseHashes, attackHashes, args.defense)

                resultScores = sorted(resultScores, key=itemgetter(1), reverse=True)
                previousHashes[oldHash_i] = resultScores[0][0]
                intermediateSteps.append(resultScores[0])

            print(deckOutput.outputStringFromResults(intermediateSteps))
            #deckOutput.saveStep(dataDirectory, filePrefix, str(step) + "_" + str(evolve_i), intermediateSteps)

        deckHashes = list(previousHashes)

    # recalculate the scores against the new best
    resultScores = None
    if(args.defense):
        resultScores = simulator.getAttackScores(resultsDb, None, enemyHashes, args.defense)
    else:
        resultScores = simulator.getAttackScores(resultsDb, enemyHashes, None, args.defense)
    resultScores = sorted(resultScores, key=itemgetter(1), reverse=True)
    if(len(resultScores) > 20):
        resultScores = resultScores[0:20]
    #outputFile = filePrefix + str(step) + ".txt"
    deckOutput.saveStep(dataDirectory, args.dataPrefix, str(step), resultScores)

def main():
    #TODO turn the common filter into a flag    
    argParser = argparse.ArgumentParser(description='Run a series of deck simulations.')
    argParser.add_argument('-c', '--cardsFile', default='cards.xml', help='file containing card xml data')
    argParser.add_argument('-o', '--ordered', type=int, default=0, help='ordered deck')
    argParser.add_argument('--outputDir', default='evolution/data/', help='directory to store results')
    argParser.add_argument('-O', '--owned', type=int, default=0, help='use owned cards as a filter')
    argParser.add_argument('-D', '--defense', type=int, default=0, help='start on defense (1) or offense (0)')
    argParser.add_argument('-p', '--dataPrefix', default='evolution', help='name for evolution set')
    argParser.add_argument('--ownedFile', default='wildcard/ownedcards.txt', help='file containing owned cardlist')
    argParser.add_argument('--defenseFile', help='file containing defense decks')
    argParser.add_argument('startStep', type=int, default=0, help='start from this evolution step')
    argParser.add_argument('endStep', type=int, default=2, help='end at this evolution step (exclusive)')
    argParser.add_argument('-d', '--numDecks', type=int, default=10, help='number of decks to evolve')
    argParser.add_argument('-n', '--numSims', type=int, default=100, help='number of simulations per comparison')

    args = argParser.parse_args()
    
    #decksToEvolve = args.numDecks
    startStep = args.startStep
    endStep = args.endStep
    #iterationsPerSimulation = args.numSims
    
    ignoreCommons = True
    ignoreActions = True

    cards = cardLoader.loadCardsWithArgs(args)
    
    ownedCards = []
    ownedCardsSet = set()
    if(args.owned):
        ownedCards = cardLoader.loadCardsFromNameFile(args.ownedFile, cards)
        ownedCardsSet = set(ownedCards.elements())    

    [commanderIds, playedIds, uniqueIds, legendaryIds] = cardLoader.getIdsFromCardData(cards, ownedCardsSet, ignoreActions, ignoreCommons)

    numberOfPlayedCards = 10
    replacementSets = deckBuilder.createReplacementSets(playedIds, numberOfPlayedCards)

    #args line

    dataDirectory = args.outputDir + args.dataPrefix + "/" #TODO verify directory exists
    useDefenseFile = args.defenseFile != None
    enemyHashes = []
    
    if(useDefenseFile):
        enemyHashes = cardLoader.loadHashesFromFile(args.defenseFile)

    resultsDb = {}
    for step in range(startStep, endStep):
        runStep(step, args, resultsDb, replacementSets, ownedCards, commanderIds, playedIds, uniqueIds, legendaryIds)
    '''
        print("Starting step " + str(step))
        stepFile = dataDirectory + args.dataPrefix + str(step) + ".txt"
        if(os.path.exists(stepFile)):
            print("\t... Step " + str(step) + " file found. Skipping...")
            continue;

        replacementOffset = step % len(replacementSets)
        print("\t... replacementOffset: " + str(replacementOffset))

        deckHashes = []
        if step == 0:
            for deck_i in range(0, 1):
                randomDeck = deckBuilder.randomDeck(commanderIds, playedIds, legendaryIds, uniqueIds)
                deckHashes.append(deckHasher.deckToHash(randomDeck))

            if(not useDefenseFile):
                enemyHashes = list(deckHashes)
            if(args.defense):
                resultsDb = simulator.runSimulationMatrix(enemyHashes, deckHashes, args.numSims, resultsDb)
                resultScores = simulator.getAttackScores(resultsDb, deckHashes, enemyHashes, args.defense)
            else:
                resultsDb = simulator.runSimulationMatrix(deckHashes, enemyHashes, args.numSims, resultsDb)
                resultScores = simulator.getAttackScores(resultsDb, enemyHashes, deckHashes, args.defense)

        else:
            previousFile = dataDirectory + args.dataPrefix + str(step - 1) + ".txt"
            previousHashes = cardLoader.loadHashesFromFile(previousFile, 1)

            for evolve_i in range(0, 11):
                print("\t... index " + str(evolve_i))
                intermediateSteps = []

                # copy this state so we do not mess with the defenses later
                if(not useDefenseFile):
                    enemyHashes = list(previousHashes)

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
                    
                    evolvedHashes = [deckHasher.deckToHash(deck) for deck in evolvedDecks]
                    #for deck in evolvedDecks:
                    #    evolvedHashes.append(deckHasher.deckToHash(deck))

                    # do not evolve if we cannot do better than the old deck
                    if(evolvedHash not in evolvedHashes):
                        evolvedHashes.append(evolvedHash)

                    if(args.defense):
                        resultsDb = simulator.runSimulationMatrix(enemyHashes, evolvedHashes, args.numSims, resultsDb)
                        resultScores = simulator.getAttackScores(resultsDb, evolvedHashes, enemyHashes, args.defense)
                    else:
                        resultsDb = simulator.runSimulationMatrix(evolvedHashes, enemyHashes, args.numSims, resultsDb)
                        resultScores = simulator.getAttackScores(resultsDb, enemyHashes, evolvedHashes, args.defense)

                    resultScores = sorted(resultScores, key=itemgetter(1), reverse=True)
                    previousHashes[oldHash_i] = resultScores[0][0]
                    intermediateSteps.append(resultScores[0])

                print(deckOutput.outputStringFromResults(intermediateSteps))
                #deckOutput.saveStep(dataDirectory, filePrefix, str(step) + "_" + str(evolve_i), intermediateSteps)

            deckHashes = list(previousHashes)

        # recalculate the scores against the new best
        resultScores = None
        if(args.defense):
            resultScores = simulator.getAttackScores(resultsDb, None, enemyHashes, args.defense)
        else:
            resultScores = simulator.getAttackScores(resultsDb, enemyHashes, None, args.defense)
        resultScores = sorted(resultScores, key=itemgetter(1), reverse=True)
        if(len(resultScores) > 20):
            resultScores = resultScores[0:20]
        #outputFile = filePrefix + str(step) + ".txt"
        deckOutput.saveStep(dataDirectory, args.dataPrefix, str(step), resultScores)
    '''

main()