"""
Requires python 2.7 or later

To use this script make sure that the cpsl compiler has been built.
Once built simply run the following from the OutputVerificationTests directory.
python verifyTestFilesOutput PATH_TO_MARS

The script currently does not support files that request input from the console.

Features:
    - Verifies that the output of a .cpsl file matches the expected output defined in a file with the name cpslFileNameResults.txt
    - Gives a print out at the end indicating which files have passed/failed
    - If either the cpsl file or the output file contain more lines than the other, then the script will output those lines which
      are missing from the appropriate file.

"""
import sys
import argparse
import os
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("marspath", help="The path to a Mars.jar file")
parser.add_argument("-pm", "--pmars", help="Writes mars output to the console", action="store_true")
parser.add_argument("-v", "--verbose", help="Prints additional details during matching", action="store_true")
parser.add_argument("-c", "--cpslpath", type=str, default=None)
args = parser.parse_args()


def printMissingContaining(lOut, sOut, isMissing):
    """
    Description: Compares sOut to lOut and prints missing and addition information from the source program's output
    Arguments: lOut - Larger output list
               sOut - Smaller output list
               isMissing - Flag that is used to determine whether or not output is missing from the source program
    Return: N/A
    """
    for ln, ele in enumerate(lOut, start=1):
        if ele not in sOut:
            if isMissing:
                print "\tMissing:   " + str(ln) + ": " + ele
            else:
                print "\tAddition:  " + str(ln) + ": " + ele
        else:
            print "\tContains:  " + str(ln) + ": " + ele
            sOut.remove(ele)


def compareOutputs(sourceOutput, expectedOutput):
    """
    Description: Compares the sourceOutput and expectedOutput lists
    Arguments: sourceOutput - The output generated by mars
               expectedOutput - The expected output returned by generateExpectedOutputList
    Return: True when both the sourceOutput and expectedOutput lists contain positionally equal elements, False otherwise.
    """
    print "The length of the program's output is as expected\n"
    for i, e in enumerate(expectedOutput):
        if e != sourceOutput[i]:
            print "\tInvalid output at line " + str(i + 1) + ": " + e + "\n\tExpected: " + sourceOutput[i] + "\n"
            return False
        elif args.verbose:
            print "\tThe line " + str(i + 1) + ": " + sourceOutput[i] + " is as expected"
    return True


def doMatching(sourceOutput, expectedOutput, path):
    """
    Description: Begins the comparison process between the sourceOutput and the expectedOutput
    Arguments: sourceOutput - The output generated by mars
               expectedOutput - The output returned by generateExpectedOutputList
               path - The path of the source program which is used for more detailed printing
    Return: N/A
    """
    lenOfSource = len(sourceOutput)
    lenOfCorrect = len(expectedOutput)

    if lenOfSource != lenOfCorrect:
        print "The length of the program's output is " + str(lenOfSource) + " but expected a length of " + str(lenOfCorrect)
        if lenOfSource > lenOfCorrect:
            print "Output of " + path + " is longer than the expected"
            printMissingContaining(sourceOutput, expectedOutput, False)
        else:
            print "Output of " + path + " is shorter than expected"
            printMissingContaining(expectedOutput, sourceOutput, True)
        return False
    else:
        return compareOutputs(sourceOutput, expectedOutput)


def generateExpectedOutputList(expectedOutputPath):
    """
    Description: Generates a list from an expected output file
    Arguments: expectedOutputPath - The path of the expected output file
    Return: expectedOutput - A list containing the expected output
    """
    expectedOutput = []
    try:
        with open(expectedOutputPath) as f:
            for line in f:
                expectedOutput.append(line.rstrip("\n"))
    except IOError as e:
        print "I/O error({0}): {1}".format(e.errno, e.strerror) + " " + expectedOutputPath
    return expectedOutput


def printPassFailLst(passLst, failLst):
    """
    Description: Prints all cpsl files which passed and failed
    Arguments: passList - A list of all the cpsl files which passed
               failList - A list of all the cpsl files which failed
    Return: N/A
    """
    if passLst:
        print "Files that passed"
        for ele in passLst:
            print "\t" + ele

    if failLst:
        print "Files that did not pass"
        for ele in failLst:
            print "\t" + ele


def attemptCompiling(path):
    """
    Description: Attempts to compile a cpsl file
    Arguments: path - The path of a cpsl file
    Return: True if the compiler succeeded, false otherwise
    """

    compilerOutput = None

    print "Attempting to compile " + path
    if args.cpslpath:
        compilerOutput = subprocess.check_output([args.cpslpath, path])
    else:
        if not os.path.exists("../../cpsl"):
            print "cpsl does not exist. Did you forget to build the compiler?"
            print "Exiting program"
            sys.exit()

        compilerOutput = subprocess.check_output(["../.././cpsl", path])

    if not compilerOutput:
        print "Successfully compiled " + path + "\n"
        return True
    else:
        print "Failed to compile " + path + " with error " + compilerOutput + "\n"
        return False


def executeMars():
    """
    Description: Executes mars on out.asm which is generated by the cpsl compiler and stores the output.
    Arguments: N/A
    Return: marsOutput - The output of mars
    """
    env = dict(os.environ)
    env['JAVA_OPTS'] = 'cpslmars'

    print "Attempting to execute asm file in mars"
    marsOutput = subprocess.check_output(["java", "-jar", args.marspath, "out.asm"], env=env)

    if args.pmars:
        print marsOutput
    print "Finished executing asm file in mars\n"

    return marsOutput


def start():
    """
    Description: Initiates comparison of all available cpsl programs with expected output files.
    Arguments: N/A
    Return: N/A
    """
    passLst = []
    failLst = []
    for subdir, dirs, files in os.walk('CpslFiles'):
        for f in files:
            if f[-4:] != "cpsl":
                continue

            path = os.path.join(subdir, f)
            print "---------------------------------------------------------------------------"

            if attemptCompiling(path):
                expectedOutputPath = "TestFilesCorrectOutput/" + f[0:-5] + "_ExpectedOutput.txt"

                sourceOutput = executeMars().split("\n")[2:-1]
                expectedOutput = generateExpectedOutputList(expectedOutputPath)

                if not expectedOutput:
                    failLst.append(f)
                    continue

                print "Beginning comparison of " + path + " with " + expectedOutputPath + "\n"

                if doMatching(sourceOutput, expectedOutput, path):
                    print "The source program's output is as expected"
                    passLst.append(f)
                else:
                    print "The source program's output does not match the expected output"
                    failLst.append(f)

                print "\nFinished comparison of " + path + "\n"
            else:
                failLst.append(f)

            print "---------------------------------------------------------------------------\n"

    printPassFailLst(passLst, failLst)

if __name__ == "__main__":
    start()