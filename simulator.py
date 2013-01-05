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

def runGroup(groupArgs, attackHashes, versusId, resultsDb):
    regexString  = "\D+(\d+)\D+(\d+)"  # Wins  123 / 200
    regexString += "\D+(\d+)\D+\d+" # Losses    123 / 200
    regexString += "\D+(\d+)\D+\d+" # Draws    123 / 200
    resultRegex = re.compile(regexString)

    for attackHash in attackHashes:
        #deckResult = [attackHash, 0]

        attackArgs = list(groupArgs)
        attackArgs = simulatorArgsAddHash(attackArgs, attackHash)
        result = runSimulation(attackArgs)

        simResults = resultRegex.match(result).groups()
        #print(simResults)
        resultsDatabase.recordResults(str(versusId), attackHash, simResults, resultsDb)

    return resultsDb

def runMatrix(attackHashes, versusMatrix, n, ordered = False, surge = False, resultsDb = None):
    args = simulatorArgsBase()
    args = simulatorArgsAddSeed(args)
    args = simulatorArgsAddNumSims(args, n)

    if(ordered):
        args = simulatorArgsAddOrdered(args);

    for versusType in versus:
        versusIds = versus[versusType]
        for versusId in versusIds:
            args = simulatorArgsAddVersus(args, versusType, versusId)
            resultsDb = runGroup(args, attackHashes, versusId, resultsDb)

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

def runSimulationsAgainstDefenses(attackHash, defenseHashes, n, resultsDb = None):
    regexString  = "\D+(\d+)\D+(\d+)"  # Wins  123 / 200
    regexString += "\D+(\d+)\D+\d+" # Losses    123 / 200
    regexString += "\D+(\d+)\D+\d+" # Draws    123 / 200
    resultRegex = re.compile(regexString)
    
    simulationCap = 10000

    args = simulatorArgsBase()
    args = simulatorArgsAddSeed(args)
    args = simulatorArgsAddNumSims(args, n)

    versusType = "hash"
    
    for defense_i in range(0, len(defenseHashes)):
        defenseHash = defenseHashes[defense_i]
        dbRow = []
#        print(attackHash + " vs " + defenseHash)
        if((not defenseHash in resultsDb) or (not attackHash in resultsDb[defenseHash]) or (resultsDb[defenseHash][attackHash][0] < simulationCap)):
            simArgs = list(args)
            simArgs = simulatorArgsAddHash(simArgs, attackHash)
            simArgs = simulatorArgsAddVersus(simArgs, versusType, defenseHash)
            result = runSimulation(simArgs)
        else:
            print("Skipping " + attackHash + " \tversus " + defenseHash)
            continue
        simResults = resultRegex.match(result).groups()
        resultsDatabase.recordResults(defenseHash, attackHash, simResults, resultsDb)
    return resultsDb

def runSimulationMatrix(attackHashes, defenseHashes, n, resultsDb = None):
    outputCounter = 0
    batchCount = len(defenseHashes) * n
    totalSimulations = len(attackHashes) * batchCount
    stepCount = int(totalSimulations / 10)
    if(stepCount < 100000): stepCount = 100000
    
    if(resultsDb is None):
        resultsDb = {}

    print("running simulation matrix with " + str(len(attackHashes)) + "x" + str(len(defenseHashes)) + "x" + str(n) + "=" + str(totalSimulations) + " simulations left")
    for attackHash in attackHashes:
        if(outputCounter >= stepCount or outputCounter == 0):
            print("simulations remaining: \t" + str(totalSimulations))
            outputCounter -= stepCount
        outputCounter += batchCount
        totalSimulations -= batchCount
        resultsDb = runSimulationsAgainstDefenses(attackHash, defenseHashes, n, resultsDb)
        
    return resultsDb
