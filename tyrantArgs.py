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

def getArgs():
    #TODO turn the common filter into a flag
    argParser = argparse.ArgumentParser(description='Run a series of deck simulations.')
    argParser.add_argument('-c', '--ignoreCommanders', default=0, help='skip over commander index')
    argParser.add_argument('-d', '--numDecks', type=int, default=10, help='number of decks to evolve')
    argParser.add_argument('-D', '--defense', type=int, nargs='?', default=0, const=1, help='start on defense (1) or offense (0)')
    argParser.add_argument('-m', '--missionId', type=int, help='id of mission to target; note that this is different than "mission 190"')
    argParser.add_argument('-n', '--numSims', type=int, default=100, help='number of simulations per comparison')
    argParser.add_argument('-o', '--ordered', type=int, nargs='?', default=0, const=1, help='ordered deck')
    argParser.add_argument('-O', '--owned', type=int, nargs='?', default=0, const=1, help='use owned cards as a filter')
    argParser.add_argument('-p', '--prefix', default='default', help='name for evolution set')
    argParser.add_argument('-Q', '--questId', nargs='+', type=int, help='id of quest to target; note that this typically matches Quest Step')
    argParser.add_argument('-r', '--raidId', type=int, help='id of raid to target')
    argParser.add_argument('-s', '--surge', type=int, nargs='?', default=0, const=1, help='attack deck surges')
    argParser.add_argument('--cardsFile', default='cards.xml', help='file containing card xml data')
    argParser.add_argument('--defenseFile', help='file containing defense decks')
    argParser.add_argument('--ignoreActions', type=int, nargs='?', default=0, help='Do not use action cards')
    argParser.add_argument('--ignoreCommons', type=int, nargs='?', default=1, help='Do not use commons')
    argParser.add_argument('--outputDir', default='evolution/data/', help='directory to store results')
    argParser.add_argument('--ownedFile', default='wildcard/ownedcards.txt', help='file containing owned cardlist')
    #argParser.add_argument('--startStep', type=int, default=0, help='start from this evolution step')
    argParser.add_argument('stepCount', type=int, default=2, help='run this many steps')

    args = argParser.parse_args()
    return args

def processPrefix(args):
    if(args.prefix == 'default'):
        if(args.missionId != None):
            args.prefix = "mission%02d" % args.missionId
        elif(args.raidId != None):
            args.prefix = "raid%02d" % args.raidId
        elif(args.questId != None):
            if(len(args.questId) == 1):
                args.prefix = "quest%02d" % args.questId[0]
            else:
                args.prefix = "quests"

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

    #args.outputDir += args.prefix + "/" #TODO verify directory exists
    
    print("using prefix: " + args.prefix)
    #if(args.prefix[:-1] != "_"):
    #    args.prefix += "_"
    #return prefix

def getOutputDir(args):
    return args.outputDir + args.prefix + "/" #TODO verify directory exists

def getOutputFile(args, step):
    return args.prefix + "_" + str(step) + ".txt"

def getVersus(args):
    versus = {}

    if(args.defenseFile != None):
        versus["hash"] = cardLoader.loadHashesFromFile(args.defenseFile)

    if(args.missionId != None):
        versus["mission"] = [args.missionId]

    if(args.questId != None):
        versus["quest"] = args.questId

    if(args.raidId != None):
        versus["raid"] = [args.raidId]

    return versus
