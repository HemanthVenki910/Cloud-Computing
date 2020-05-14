# REG 0 - 7 are the available Registers
# Use the Sub Routines to execute Operations

import sys

if len(sys.argv) != 2:
    print("Correct usage: Enter filename\n")
    exit()

def printcode(list_of_lines, message=""):
    print(message.upper())
    for line in list_of_lines:
        print(line.strip())

if __name__ == "__main__":

    if len(sys.argv) == 2:
        optimized_code = str(sys.argv[1])

    list_of_lines = []
    f = open(optimized_code, "r")
    for line in f:
        list_of_lines.append(line)
    f.close()

    printcode(list_of_lines)