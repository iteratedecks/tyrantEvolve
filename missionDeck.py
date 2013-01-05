import argparse
from operator import itemgetter
import os
import xml.sax

import deckBuilder
import deckHasher
import deckOutput
import cardLoader
import simulator

def main():
    argParser = argparse.ArgumentParser(description='Run a series of deck simulations against a raid deck.')
    argParser.add_argument('-c', '--cardsFile', default='cards.xml', help='file containing card xml data')
    argParser.add_argument('-O', '--owned', type=int, default=0, help='use owned cards as a filter')
    argParser.add_argument('-o', '--ordered', type=int, default=0, help='ordered deck')
    argParser.add_argument('--outputDir', default='evolution/data/', help='directory to store results')
    argParser.add_argument('--ownedFile', default='wildcard/ownedcards.txt', help='file containing owned cardlist')
    argParser.add_argument('missionId', type=int, default=1, help='id of mission to target; note that this is different than "mission 190"')
    argParser.add_argument('--prefix', default='default', help='name for data set')
    argParser.add_argument('startStep', type=int, default=0, help='start from this evolution step')
    argParser.add_argument('endStep', type=int, default=2, help='end at this evolution step (exclusive)')
    argParser.add_argument('-d', '--numDecks', type=int, default=1, help='number of decks to evolve')
    argParser.add_argument('-n', '--numSims', type=int, default=100, help='number of simulations per comparison')
    argParser.add_argument('-s', '--surge', type=int, default=0, help='attack deck surges')
    argParser.add_argument('--ignoreActions', type=int, default=0, help='Do not use action cards')
    argParser.add_argument('--ignoreCommons', type=int, default=0, help='Do not use commons')

    args = argParser.parse_args()

    iterationsPerSimulation = args.numSims
    useOwnedFilter = args.owned
    
    startStep = args.startStep
    endStep = args.endStep

    numberOfPlayedCards = 10

    filePrefix = args.prefix
    if(filePrefix == 'default'):
        filePrefix = "mission"
        filePrefix += "%02d" % args.missionId
        if(args.ordered):
            filePrefix += "o"
        if(args.surge):
            filePrefix += "s"

    dataDirectory = args.outputDir
    dataDirectory += "missions/"
    dataDirectory += filePrefix + "/" #TODO verify directory exists
    
    filePrefix += "_"
    
    cards = cardLoader.loadCardsWithArgs(args)

    ownedCards = []
    ownedCardsSet = set()
    if(args.owned):
        ownedCards = cardLoader.loadCardsFromNameFile(args.ownedFile, cards)
        ownedCardsSet = set(ownedCards.elements())

    [commanderIds, playedIds, uniqueIds, legendaryIds] = cardLoader.getIdsFromCardData(cards, ownedCardsSet, args.ignoreActions, args.ignoreCommons)

    replacementSets = deckBuilder.createReplacementSets(playedIds, numberOfPlayedCards)

    resultsDb = {}
    for step in range(startStep, endStep):
        print("Starting step " + str(step))
        stepFile = dataDirectory + filePrefix + str(step) + ".txt"
        if(os.path.exists(stepFile)):
            print("\t... Step " + str(step) + " file found. Skipping...")
            continue;

        replacementOffset = step % len(replacementSets)
        print("\t... replacementOffset: " + str(replacementOffset))

        deckHashes = []
        if step == 0:
            for deck_i in range(0, args.numDecks):
                randomDeck = deckBuilder.randomDeck(commanderIds, playedIds, legendaryIds, uniqueIds)
                deckHashes.append(deckHasher.deckToHash(randomDeck))
            resultsDb = simulator.runMissionGroup(deckHashes, args.missionId, iterationsPerSimulation, ordered, surge, resultsDb)

        else:
            previousFile = dataDirectory + filePrefix + str(step - 1) + ".txt"
            previousHashes = cardLoader.loadHashesFromFile(previousFile, 1)

            for evolve_i in range(0, 11):
                print("\t... index " + str(evolve_i))
                #intermediateSteps = []

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
                        if(swap_index != evolve_i):
                            #print("swapping " + str(evolve_i) + " for " + str(swap_index))
                            evolvedDecks.extend(deckBuilder.orderSwap(evolvedDeck, evolve_i, range(swap_index, swap_index + 1)))
                    
                    evolvedHashes = [deckHasher.deckToHash(deck) for deck in evolvedDecks]
                    #for deck in evolvedDecks:
                    #    evolvedHashes.append(deckHasher.deckToHash(deck))

                    # do not evolve if we cannot do better than the old deck
                    if(evolvedHash not in evolvedHashes):
                        evolvedHashes.append(evolvedHash)

                    resultsDb = simulator.runMissionGroup(evolvedHashes, args.missionId, iterationsPerSimulation, args.ordered, args.surge, resultsDb)
                    resultScores = simulator.getAttackScores(resultsDb, [str(args.missionId)], evolvedHashes, False)

                    resultScores = sorted(resultScores, key=itemgetter(1), reverse=True)
                    previousHashes[oldHash_i] = resultScores[0][0]
                    #intermediateSteps.append(resultScores[0])

                #deckOutput.saveStep(dataDirectory, filePrefix, str(step) + "_" + str(evolve_i), intermediateSteps)

            deckHashes = list(previousHashes)

        # recalculate the scores against the new best
        resultScores = simulator.getAttackScores(resultsDb, [str(args.missionId)], None, False)
        resultScores = sorted(resultScores, key=itemgetter(1), reverse=True)
        if(len(resultScores) > 20):
            resultScores = resultScores[0:20]
        #outputFile = filePrefix + str(step) + ".txt"
        deckOutput.saveStep(dataDirectory, filePrefix, str(step), resultScores)

main()