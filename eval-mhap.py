#!/usr/bin/python

import os, sys, getopt, re, json

def main():

    options = "i:o:b:l:g:j:h"
    long_options = ["help"]

    in_path = None
    out_path = None
    bwa_path = None
    last_path = None
    graphmap_path = None
    joint_path = None

    try:
        opts, args = getopt.getopt(sys.argv[1:], options, long_options)
    except getopt.GetoptError as err:
        print(str(err))
        help()
        sys.exit()

    for option, argument in opts:
        if option in ("-i"):
            in_path = argument
        elif option in ("-o"):
            out_path = argument
        elif option in ("-b"):
            bwa_path = argument
        elif option in ("-l"):
            last_path = argument
        elif option in ("-g"):
            graphmap_path = argument
	elif option in ("-j"):
            joint_path = argument
        elif option in ("-h", "-help"):
            help()
            sys.exit()

    if in_path is None:
        error("missing option: -i <input overlaps file>")

    if not os.path.isfile(in_path):
        error("non-existent file: -i {}".format(in_path))

    if out_path is None:
        error("mising option: -o <out file>")

    if last_path is None:
        error("missing option: -l <last json file>")

    if not os.path.isfile(last_path):
        error("non-existent file: -l {}".format(last_path))

    if bwa_path is None:
        error("missing option: -b <bwa json file>")

    if not os.path.isfile(bwa_path):
        error("non-existent file: -b {}".format(bwa_path))

    if graphmap_path is None:
        error("missing option: -g <graphmap json file>")

    if not os.path.isfile(graphmap_path):
        error("non-existent file: -g {}".format(graphmap_path))

    last_dict = loadDictionary(last_path)
    bwa_dict = loadDictionary(bwa_path)
    graphmap_dict = loadDictionary(graphmap_path)
    joint_dict = loadDictionary(joint_path)

    overlaps = parseMhapFile(in_path)
    labelOverlaps(overlaps, last_dict, bwa_dict, graphmap_dict, out_path)

def loadDictionary(file_path):
    dictionary = None
    with open(file_path) as file:
        dictionary = json.load(file)
    return dictionary

def labelOverlaps(overlaps, last_dict, bwa_dict, graphmap_dict, out_path):

    last_t = 0
    bwa_t = 0
    graphmap_t = 0
    total_t = 0
    last_f = 0
    bwa_f = 0
    graphmap_f = 0
    total_f = 0

    faulty_overlaps = []
    correct_overlaps = []

    for overlap in overlaps:
        true = 0
        if (overlap[0] in last_dict and int(overlap[1]) in last_dict[overlap[0]]) or (overlap[1] in last_dict and int(overlap[0]) in last_dict[overlap[1]]):
            last_t += 1
            true = 1
        else:
            last_f += 1
        if (overlap[0] in bwa_dict and int(overlap[1]) in bwa_dict[overlap[0]]) or (overlap[1] in bwa_dict and int(overlap[0]) in bwa_dict[overlap[1]]):
            bwa_t += 1
            true = 1   
        else:
            bwa_f += 1
        if (overlap[0] in graphmap_dict and int(overlap[1]) in graphmap_dict[overlap[0]]) or (overlap[1] in graphmap_dict and int(overlap[0]) in graphmap_dict[overlap[1]]):
            graphmap_t += 1
            true = 1
        else:
            graphmap_f += 1
        if true == 1:
            total_t += 1
            correct_overlaps.append(overlap[3])
        else:
            total_f += 1
            faulty_overlaps.append(overlap[3])

    print("Last (T,F,Prec(%%),Rec(%%): %d, %d, %f, %f" % (last_t, last_f, float(last_t) / (last_t + last_f), last_t / float(last_dict["total"])))
    print("Bwa (T,F,Prec(%%),Rec(%%)): %d, %d, %f, %f" % (bwa_t, bwa_f, float(bwa_t) / (bwa_t + bwa_f), bwa_t / float(bwa_dict["total"])))
    print("Graphmap (T,F,Prec(%%),Rec(%%)): %d, %d, %f, %f" % (graphmap_t, graphmap_f, float(graphmap_t) / (graphmap_t + graphmap_f), graphmap_t / float(graphmap_dict["total"])))
    print("Total (T,F): %d, %d" % (total_t, total_f))

    with open(out_path + "_true.mhap", "w") as file:
        for overlap in correct_overlaps:
            file.write(overlap + '\n')
    with open(out_path + "_false.mhap", "w") as file:
        for overlap in faulty_overlaps:
            file.write(overlap + '\n')

def parseMhapFile(file_path):
    input = open(file_path).read().split("\n")

    i = -1
    input_len = len(input)
    overlaps = []

    while (1):
        i += 1
        if (i == input_len):
            break

        if (input[i] == ""):
            continue

        # alignment lines
        tabs = input[i].split()
        id_a = tabs[0]
        id_b = tabs[1]
        rk = 1 if tabs[4] != tabs[8] else 0

        overlaps.append([id_a, id_b, rk, input[i]])

    return overlaps

def error(message):
    print("[ERROR] {}".format(message))
    sys.exit()

def help():
    print(
    "usage: python label_overlaps.py [arguments ...]\n"
    "arguments:\n"
    "    -i  <input overlaps file>\n"
    "        (required)\n"
    "        file containing read overlaps in MHAP (MinHash Alignment Process) format\n"
    "    -o  <out path>\n"
    "        (required)\n"
    "        creates a file containing faulty overlaps and a file containing correct\n"
    "        overlaps in MHAP format (_faulty.mhap and _correct.mhap)\n"
    "    -l  <last json file>\n"
    "        (required)\n"
    "        file containing alignments dictionary of LAST in JSON format\n"
    "    -b  <bwa json file>\n"
    "        (required)\n"
    "        file containing alignments dictionary of BWA in JSON format\n"
    "    -g  <graphmap json file>\n"
    "        (required)\n"
    "        file containing alignments dictionary of GraphMap in JSON format\n"
    "    -h, --help\n"
    "        prints out the help")

if __name__ == "__main__":
    main()
