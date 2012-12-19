#!/Applications/Python/python.exe
import argparse
import simulator
from operator import itemgetter

def loadHashesFromFile(file):
    hashes = []
    f = open(file, 'r')
    for line in f:
        line = line.strip()
        if(len(line) == 0 or line[0] == "#"): continue
        hashes.append(line.split('\t')[0])
    f.close()
    return hashes

def main():
    argParser = argparse.ArgumentParser(description='Run a series of deck simulations.')
    argParser.add_argument('attackFile', help='load attack hashes from this file')
    argParser.add_argument('defenseFile', help='load defense hashes from this file')
    argParser.add_argument('-n', '--numSims', type=int, default=100, help='number of simulations per comparison')
    argParser.add_argument('-D', '--defense', type=int, default=0, help='start on defense (1) or offense (0)')

    args = argParser.parse_args()

    iterationsPerSimulation = args.numSims
    attackFile = args.attackFile
    defenseFile = args.defenseFile
    scoreAsDefense = args.defense == 1

    attackHashes = loadHashesFromFile(attackFile)
    defenseHashes = loadHashesFromFile(defenseFile)
    
    resultsDb = {}
    if(scoreAsDefense):
        resultsDb = simulator.runSimulationMatrix(defenseHashes, attackHashes, iterationsPerSimulation, resultsDb)
        resultScores = simulator.getAttackScores(resultsDb, attackHashes, defenseHashes, scoreAsDefense)
    else:
        resultsDb = simulator.runSimulationMatrix(attackHashes, defenseHashes, iterationsPerSimulation, resultsDb)
        resultScores = simulator.getAttackScores(resultsDb, defenseHashes, attackHashes, scoreAsDefense)

    outputString = "\n"
    for key in resultsDb:
        outputString += key + "\n"
        for inner_key in resultsDb[key]:
            outputString += "\t" + inner_key + "\t" + "\t".join(map(str, resultsDb[key][inner_key])) + "\n"

    resultScores = None
    if(scoreAsDefense):
        resultScores = simulator.getAttackScores(resultsDb, None, defenseHashes, scoreAsDefense)
    else:
        resultScores = simulator.getAttackScores(resultsDb, defenseHashes, None, scoreAsDefense)

    '''
    attackScores = {}
    for defenseHash in defenseHashes:
        results = resultsDb[defenseHash]
        for attackHash in results:
            if(not attackHash in attackScores):
                attackScores[attackHash] = [attackHash, 0, 0]
            attackScores[attackHash][1] += results[attackHash][1]
            attackScores[attackHash][2] += results[attackHash][0]
            attackScores[attackHash].append(results[attackHash][1] / results[attackHash][0])
    '''
    
    outputString += "\n"
    scores = sorted(resultScores, key=itemgetter(1), reverse=True)
    for score in scores:
        outputString += "\t".join(map(str, score)) + "\n"
    print(outputString)

main()
