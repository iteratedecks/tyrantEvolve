from operator import itemgetter
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

def getVersusScores(resultsDb, evolvedHashes, versus, defense = False):
    attackKeys = evolvedHashes
    defenseKeys = resultsDatabase.getVersusKeys(versus)
    resultScores = None
    if("hash" in versus and len(versus["hash"]) > 0):
        if(defense):
            attackKeys = defenseKeys
            defenseKeys = evolvedHashes

    resultScores = getAttackScores(resultsDb, defenseKeys, attackKeys, defense)
    resultScores = sorted(resultScores, key=itemgetter(1), reverse=True)
    return resultScores

def getAttackScores(resultsDb, defenseHashes, attackHashes, scoreDefense = False):
    useAllAttackHashes = (attackHashes is None)
    if(defenseHashes is None):
        defenseHashes = resultsDb.keys()

    attackScores = {}
    resultHash = None
    for defenseHash in defenseHashes:
        if(not defenseHash in resultsDb):
            print("Warning: " + defenseHash + " is not in results")
            continue

        #print("defenseHash: '" + defenseHash + "'")

        results = resultsDb[defenseHash]
        if(scoreDefense):
            resultHash = defenseHash
        if(useAllAttackHashes):
            attackHashes = results.keys()

        for attackHash in attackHashes:
            if(not attackHash in results):
                print("Warning: " + attackHash + " has no results for " + defenseHash)
                continue

            #print("attackHash: '" + attackHash + "'")

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
            attackScores[resultHash][1] = float(attackScores[resultHash][2]) / attackScores[resultHash][3]
            #attackScores[resultHash].append(score / total)

            #print("attackScore: '" + "\t".join(map(str, attackScores[resultHash])) + "'")

    return attackScores.values()

def runMatrix(attackHashes, defenseMatrix, n, ordered = False, surge = False, resultsDb = None):
    
    if(resultsDb is None):
        resultsDb = {}

    args = simulatorArgsBase()
    args = simulatorArgsAddSeed(args)
    args = simulatorArgsAddNumSims(args, n)

    if(ordered):
        args = simulatorArgsAddOrdered(args)

    if(surge):
        args = simulatorArgsAddSurge(args)

    attackCount = len(attackHashes)

    # wins total losses draws
    regexString  = "\D+(\d+)\D+(\d+)"  # Wins  123 / 200
    regexString += "\D+(\d+)\D+\d+" # Losses    123 / 200
    regexString += "\D+(\d+)\D+\d+" # Draws    123 / 200
    resultRegex = re.compile(regexString)

    simulationCap = 10000

    for defenseType in defenseMatrix:
        print("starting " + defenseType + " matrix... ")
        defenseIds = defenseMatrix[defenseType]

        defenseCounter = 0
        defenseCount = len(defenseIds)

        # attack loop must go first because the simulator takes ATTACKHASH DEFENSEHASH
        for attackHash in attackHashes:
            attackKey = resultsDatabase.deckKey("hash", attackHash)
            attackArgs = list(args)
            attackArgs = simulatorArgsAddHash(attackArgs, attackHash)

            #print("\tstarting attack group with attackKey " + attackKey)

            for defenseId in defenseIds:
                #totalSimulations = attackCount * (defenseCount - defenseCounter) * n
                #print("\t" + str(defenseCount - defenseCounter) + "x" + str(attackCount) + "x" + str(n) + "=" + str(totalSimulations) + " simulations left")

                defenseArgs = list(attackArgs)
                defenseArgs = simulatorArgsAddVersus(defenseArgs, defenseType, defenseId)

                defenseKey = resultsDatabase.deckKey(defenseType, defenseId)

                if((defenseKey in resultsDb) and (attackKey in resultsDb[defenseKey]) and (resultsDb[defenseKey][attackKey][0] >= simulationCap)):
                    print("Skipping " + attackKey + " \tdefense " + defenseKey)
                    continue

                #print("\t\trunning " + attackKey + " vs \t" + defenseKey)
                result = runSimulation(defenseArgs)

                simResults = resultRegex.match(result).groups()
                resultsDatabase.recordResults(defenseKey, attackKey, simResults, resultsDb)

            #defenseCounter = defenseCounter + 1

    return resultsDb

def runSimulation(args):
    result = subprocess.check_output(args)
    return result.decode()

def runVersusMatrix(versus, evolvedHashes, resultsDb, numSims, defense = False, ordered = False, surge = False):
    attackKeys = evolvedHashes
    defenseVersus = versus
    if("hash" in versus and len(versus["hash"]) > 0):
        if(defense):
            attackKeys = versus["hash"]
            defenseVersus = { "hash": evolvedHashes }
        #    attackKeys = evolvedHashes
        #    defenseVersus = versus
        #resultsDb = simulator.runSimulationMatrix(attackKeys, defenseHashes, args.numSims, resultsDb)

    resultsDb = runMatrix(attackKeys, defenseVersus, numSims, ordered, surge, resultsDb)
    #defenseKeys = resultsDatabase.getVersusKeys(defenseVersus)
    #resultScores = getAttackScores(resultsDb, defenseKeys, attackKeys, defense)
    #resultScores = sorted(resultScores, key=itemgetter(1), reverse=True)
    return getVersusScores(resultsDb, None, versus, defense)
