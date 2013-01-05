import re
import resultsDatabase
import subprocess

# this path is relative to the working directory; you should
# call these scripts from the same directory that contains the simulator
simulatorPath = "iteratedecks-cli.exe"

def simulatorArgsBase(attackHash = None, defenseHash = None, path = simulatorPath):
    args = [path]
    if(attackHash):
        args.append(attackHash)
    if(defenseHash):
        args.append(defenseHash)
    return args

def simulatorArgsAddHash(args, deckHash):
    args.append(deckHash)
    return args

def simulatorArgsAddMission(args, missionId):
    args.extend(["-m", str(missionId)])
    return args

def simulatorArgsAddNumSims(args, n):
    args.extend(["-n", str(n)])
    return args

def simulatorArgsAddOrdered(args):
    args.extend(["-o"])
    return args

def simulatorArgsAddQuest(args, questId):
    args.extend(["-Q", str(questId)])
    return args

def simulatorArgsAddRaid(args, raidId):
    args.extend(["-r", str(raidId)])
    return args

def simulatorArgsAddSeed(args):
    args.extend(["--seed"])
    return args

def simulatorArgsAddSurge(args):
    args.extend(["-s"])
    return args

def simulatorArgsAddVersus(args, versusType, versusId):
    if(versusType == "quest"):
        args = simulatorArgsAddQuest(args, versusId)
    elif(versusType == "mission"):
        args = simulatorArgsAddMission(args, versusId)
    elif(versusType == "raid"):
        args = simulatorArgsAddRaid(args, versusId)
    elif(versusType == "hash"):
        args = simulatorArgsAddHash(args, versusId)
    return args

def getAttackScores(resultsDb, defenseHashes, attackHashes, scoreDefense = False):
    useAllAttackHashes = (attackHashes is None)
    if(defenseHashes is None):
        defenseHashes = resultsDb.keys();

    attackScores = {}
    resultHash = None
    for defenseHash in defenseHashes:
        if(not defenseHash in resultsDb):
            print("Warning: " + defenseHash + " is not in results")
            continue

        results = resultsDb[defenseHash]
        if(scoreDefense):
            resultHash = defenseHash
        if(useAllAttackHashes):
            attackHashes = results.keys()
        for attackHash in attackHashes:
            if(not attackHash in results):
                print("Warning: " + attackHash + " has no results for " + defenseHash)
                continue

            if(not scoreDefense):
                resultHash = attackHash

            total = results[attackHash][0]
            wins = results[attackHash][1]
            losses = results[attackHash][2]
            draws = results[attackHash][3]
            score = wins
            if(scoreDefense):
                score = losses + draws
                
            if(not resultHash in attackScores):
                attackScores[resultHash] = [resultHash, 0, 0, 0, 0, 0, 0]

            attackScores[resultHash][2] += score
            attackScores[resultHash][3] += total
            attackScores[resultHash][4] += wins
            attackScores[resultHash][5] += losses
            attackScores[resultHash][6] += draws
            #TODO could probably move this after all the numbers were tallied
            attackScores[resultHash][1] = attackScores[resultHash][2] / attackScores[resultHash][3]
            attackScores[resultHash].append(score / total)

    return attackScores.values()

def runAttackGroup(groupArgs, attackHashes, versusId, resultsDb):
    regexString  = "\D+(\d+)\D+(\d+)"  # Wins  123 / 200
    regexString += "\D+(\d+)\D+\d+" # Losses    123 / 200
    regexString += "\D+(\d+)\D+\d+" # Draws    123 / 200
    resultRegex = re.compile(regexString)

    simulationCap = 10000

    for attackHash in attackHashes:
        if((versusId in resultsDb) and (attackHash in resultsDb[versusId]) and (resultsDb[versusId][attackHash][0] >= simulationCap)):
            print("Skipping " + attackHash + " \tversus " + versusId)
            continue

        attackArgs = list(groupArgs)
        attackArgs = simulatorArgsAddHash(attackArgs, attackHash)
        result = runSimulation(attackArgs)

        simResults = resultRegex.match(result).groups()
        resultsDatabase.recordResults(str(versusId), attackHash, simResults, resultsDb)

    return resultsDb

def runMatrix(attackHashes, versusMatrix, n, ordered = False, surge = False, resultsDb = None):
    
    if(resultsDb is None):
        resultsDb = {}

    args = simulatorArgsBase()
    args = simulatorArgsAddSeed(args)
    args = simulatorArgsAddNumSims(args, n)

    if(ordered):
        args = simulatorArgsAddOrdered(args);

    attackCount = len(attackHashes)

    for versusType in versusMatrix:
        versusIds = versusMatrix[versusType]

        versusCounter = 0
        versusCount = len(versusIds)

        print("starting " + versusType + " matrix... ")

        for versusId in versusIds:
            totalSimulations = attackCount * (versusCount - versusCounter) * n
            print("\t" + str(versusCount - versusCounter) + "x" + str(attackCount) + "x" + str(n) + "=" + str(totalSimulations) + " simulations left")

            groupArgs = list(args)
            groupArgs = simulatorArgsAddVersus(groupArgs, versusType, versusId)
            resultsDb = runAttackGroup(groupArgs, attackHashes, versusId, resultsDb)

            versusCounter = versusCounter + 1

    return resultsDb

def runQuestGroup(attackHashes, questId, n, ordered = False, resultsDb = None):
    versus = {}
    versus["quest"] = [questId]

    return runMatrix(attackHashes, versus, n, ordered, False, resultsDb)

def runMissionGroup(attackHashes, missionId, n, ordered = False, surge = False, resultsDb = None):    
    versus = {}
    versus["mission"] = [missionId]

    return runMatrix(attackHashes, versus, n, ordered, surge, resultsDb)

def runRaidGroup(attackHashes, raidId, n, ordered = False, resultsDb = None):
    versus = {}
    versus["raid"] = [raidId]

    return runMatrix(attackHashes, versus, n, ordered, False, resultsDb)

def runSimulation(args):
    result = subprocess.check_output(args)
    return result.decode()

def runSimulationMatrix(attackHashes, defenseHashes, n, resultsDb = None):
    versus = {}
    versus["hash"] = defenseHashes

    return runMatrix(attackHashes, versus, n, False, False, resultsDb)
