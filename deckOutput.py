def saveStep(dataDirectory, filePrefix, stepName, resultsMatrix):
    outputString = "# Step " + stepName + "\n"
    outputString += outputStringFromResults(resultsMatrix)

    outputFile = filePrefix + stepName + ".txt"
    
    mkdir_p(dataDirectory)
    f = open(dataDirectory + outputFile, 'w')
    f.write(outputString)
    print(outputString)
    f.close()

def saveDeckList(dataDirectory, filePrefix, stepName, resultsMatrix, header):
    outputString = "#" + header + "\n"
    outputString += outputStringFromResults(resultsMatrix)

    outputFile = filePrefix + "_" + stepName + ".txt"
    
    mkdir_p(dataDirectory)
    f = open(dataDirectory + outputFile, 'w')
    f.write(outputString)
    print(outputString)
    f.close()

def outputStringFromResults(resultsMatrix):
    outputString = ""
    for result in resultsMatrix:
        deckOutput = map(str, result)
        outputString += "\t".join(deckOutput) + "\n"
    return outputString

def mkdir_p(path):
    import os, errno
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else: raise
