#!/Applications/Python/python.exe
import re
import resultsDatabase
import subprocess

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

def runQuest(attackHash, questId, n, ordered = False):
    program = "CLI.exe"
    #program = "iteratedecks-cli.exe"
    args = [program, "--seed", attackHash, "-Q " + str(questId), "-n " + str(n)]
    if(ordered):
        args.append("-o")
    #print(args)
    result = subprocess.check_output(args)
    return result.decode()

def runQuestGroup(attackHashes, questId, n, ordered = False, resultsDb = None):
    regexString  = "\D+(\d+)\D+(\d+)"  # Wins  123 / 200
    regexString += "\D+(\d+)\D+\d+" # Losses    123 / 200
    regexString += "\D+(\d+)\D+\d+" # Draws    123 / 200
    resultRegex = re.compile(regexString)
    
    for attackHash in attackHashes:
        deckResult = [attackHash, 0]

        result = runQuest(attackHash, questId, n)
        simResults = resultRegex.match(result).groups()
        #print(simResults)
        resultsDatabase.recordResults(str(questId), attackHash, simResults, resultsDb)

    return resultsDb

def runMission(attackHash, missionId, n, ordered = False, surge = False):
    program = "CLI.exe"
    #program = "iteratedecks-cli.exe"
    args = [program, "--seed", attackHash, "-m " + str(missionId), "-n " + str(n)]
    if(ordered):
        args.append("-o")
    if(surge):
        args.append("-s")
    #print(args)
    result = subprocess.check_output(args)
    return result.decode()

def runMissionGroup(attackHashes, missionId, n, ordered = False, surge = False, resultsDb = None):
    regexString  = "\D+(\d+)\D+(\d+)"  # Wins  123 / 200
    regexString += "\D+(\d+)\D+\d+" # Losses    123 / 200
    regexString += "\D+(\d+)\D+\d+" # Draws    123 / 200
    resultRegex = re.compile(regexString)
    
    for attackHash in attackHashes:
        deckResult = [attackHash, 0]

        result = runMission(attackHash, missionId, n, ordered, surge)
        simResults = resultRegex.match(result).groups()
        #print(simResults)
        resultsDatabase.recordResults(str(missionId), attackHash, simResults, resultsDb)

    return resultsDb

def runRaid(attackHash, raidId, n, ordered = False):
    program = "CLI.exe"
    #program = "iteratedecks-cli.exe"
    args = [program, "--seed", attackHash, "-r " + str(raidId), "-n " + str(n)]
    if(ordered):
        args.append("-o")
    #print(args)
    result = subprocess.check_output(args)
    return result.decode()

def runRaidGroup(attackHashes, raidId, n, ordered = False, resultsDb = None):
    regexString  = "\D+(\d+)\D+(\d+)"  # Wins  123 / 200
    regexString += "\D+(\d+)\D+\d+" # Losses    123 / 200
    regexString += "\D+(\d+)\D+\d+" # Draws    123 / 200
    resultRegex = re.compile(regexString)
    
    for attackHash in attackHashes:
        deckResult = [attackHash, 0]

        result = runRaid(attackHash, raidId, n)
        simResults = resultRegex.match(result).groups()
        resultsDatabase.recordResults(str(raidId), attackHash, simResults, resultsDb)

    return resultsDb

def runSimulation(attackHash, defenseHash, n):
    program = "CLI.exe"
    #program = "iteratedecks-cli.exe"
    result = subprocess.check_output([program, "--seed", attackHash, defenseHash, "-n " + str(n)])
    return result.decode()

def runSimulationsAgainstDefenses(attackHash, defenseHashes, n, resultsDb = None):
    regexString  = "\D+(\d+)\D+(\d+)"  # Wins  123 / 200
    regexString += "\D+(\d+)\D+\d+" # Losses    123 / 200
    regexString += "\D+(\d+)\D+\d+" # Draws    123 / 200
    resultRegex = re.compile(regexString)
    
    simulationCap = 10000
    
    for defense_i in range(0, len(defenseHashes)):
        defenseHash = defenseHashes[defense_i]
        dbRow = []
#        print(attackHash + " vs " + defenseHash)
        if((not defenseHash in resultsDb) or (not attackHash in resultsDb[defenseHash]) or (resultsDb[defenseHash][attackHash][0] < simulationCap)):
            result = runSimulation(attackHash, defenseHash, n)
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
