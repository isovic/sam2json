#!/usr/bin/python

# Script originally implemented by Robert Vaser (2016), modified by Ivan Sovic (2016).

import os, sys, getopt, re, json

def main():

    options = "i:o:b:l:g:a:h"
    long_options = ["help"]

    in_path = None
    out_path = None
    bwa_path = None
    last_path = None
    graphmap_path = None
    joint_path = None
    csv_path = None;

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
        elif option in ("-a"):
            csv_path = argument        
    	# elif option in ("-j"):
     #        joint_path = argument
        elif option in ("-h", "-help"):
            help()
            sys.exit()

    if in_path is None:
        error("missing option: -i <input overlaps file>")

    if not os.path.isfile(in_path):
        error("non-existent file: -i {}".format(in_path))

    if out_path is None:
        error("mising option: -o <out file>")

    if (last_path == None and bwa_path == None and graphmap_path == None and joint_path == None):
        # error("At least one truth file needs to be specified, either '-l <last json file>', '-b<bwa json file>', '-g <graphmap json file>' or '-j <joint json file>'.");
        error("At least one truth file needs to be specified, either '-l <last json file>', '-b<bwa json file>' or '-g <graphmap json file>'.");

    if (last_path != None and not os.path.isfile(last_path)):
        error("non-existent file: -l {}".format(last_path))

    if (bwa_path != None and not os.path.isfile(bwa_path)):
        error("non-existent file: -b {}".format(bwa_path))

    if (graphmap_path != None and not os.path.isfile(graphmap_path)):
        error("non-existent file: -g {}".format(graphmap_path))

    # if (joint_path != None and not os.path.isfile(joint_path)):
    #     error("non-existent file: -j {}".format(joint_path))

    last_dict = loadDictionary(last_path) if (last_path != None) else None;
    bwa_dict = loadDictionary(bwa_path) if (bwa_path != None) else None;
    graphmap_dict = loadDictionary(graphmap_path) if (graphmap_path != None) else None;
#    joint_dict = loadDictionary(joint_path) if (joint_path != None) else None;

    joint_dict = merge_dicts([last_dict, bwa_dict, graphmap_dict]);

    overlaps = parseMhapFile(in_path)
    # labelOverlaps(in_path, overlaps, last_dict, bwa_dict, graphmap_dict, joint_dict, out_path, csv_path)
    labelOverlaps(in_path, overlaps, None, None, None, joint_dict, out_path, csv_path)

def loadDictionary(file_path):
    dictionary = None
    with open(file_path) as file:
        dictionary = json.load(file)
    return dictionary

def merge_dicts(dict_list):
    sys.stderr.write('Merging truth overlaps.\n');
    overlap_union = {};
    for overlap_dict in dict_list:
        if (overlap_dict == None): continue;
        for key in overlap_dict:
            if (key == 'total'): continue;
            if (not key in overlap_union):
                overlap_union[key] = [];
            overlap_union[key] += overlap_dict[key];

    if (overlap_union == {}): return None;

    total = 0;
    for key in overlap_union:
        if (key == 'total'):
            pass;
        else:
            overlap_union[key] = list(set(overlap_union[key]));
            total += len(overlap_union[key]);
    overlap_union['total'] = total/2 - len(overlap_union.keys());

    sys.stderr.write('Finished merging.\n');

    return overlap_union;

def labelOverlaps(in_path, overlaps, last_dict, bwa_dict, graphmap_dict, joint_dict, out_path, csv_path):
    if (len(overlaps) == 0):
        print ("ERROR: Input file contains *no* overlaps!");
        return None;

    last_t = 0
    bwa_t = 0
    graphmap_t = 0
    joint_t = 0;
    total_t = 0
    last_f = 0
    bwa_f = 0
    graphmap_f = 0
    joint_f = 0;
    total_f = 0
    last_unknown = 0;
    bwa_unknown = 0;
    graphmap_unknown = 0;
    joint_unknown = 0;
    total_unknown = 0;

    faulty_overlaps = []
    correct_overlaps = []
    unknown_overlaps = [];

    for overlap in overlaps:
        true = 0
        if (last_dict != None and ((overlap[0] in last_dict and int(overlap[1]) in last_dict[overlap[0]]) or (overlap[1] in last_dict and int(overlap[0]) in last_dict[overlap[1]]))):
            last_t += 1
            true = 1
        else:
            if (last_dict != None and ((int(overlap[0]) in last_dict["unmapped"]) or (int(overlap[1]) in last_dict["unmapped"]))):
                last_unknown += 1;
            else:
                last_f += 1
        if (bwa_dict != None and ((overlap[0] in bwa_dict and int(overlap[1]) in bwa_dict[overlap[0]]) or (overlap[1] in bwa_dict and int(overlap[0]) in bwa_dict[overlap[1]]))):
            bwa_t += 1
            true = 1   
        else:
            if (bwa_dict != None and ((int(overlap[0]) in bwa_dict["unmapped"]) or (int(overlap[1]) in bwa_dict["unmapped"]))):
                bwa_unknown += 1;
            else:
                bwa_f += 1

        if (graphmap_dict != None and ((overlap[0] in graphmap_dict and int(overlap[1]) in graphmap_dict[overlap[0]]) or (overlap[1] in graphmap_dict and int(overlap[0]) in graphmap_dict[overlap[1]]))):
            graphmap_t += 1
            true = 1
        else:
            if (graphmap_dict != None and ((int(overlap[0]) in graphmap_dict["unmapped"]) or (int(overlap[1]) in graphmap_dict["unmapped"]))):
                graphmap_unknown += 1;
            else:
                graphmap_f += 1

        if (joint_dict != None and ((overlap[0] in joint_dict and int(overlap[1]) in joint_dict[overlap[0]]) or (overlap[1] in joint_dict and int(overlap[0]) in joint_dict[overlap[1]]))):
            joint_t += 1
            true = 1
        else:
            if (joint_dict != None and ((int(overlap[0]) in joint_dict["unmapped"]) or (int(overlap[1]) in joint_dict["unmapped"]))):
                joint_unknown += 1;
            else:
                joint_f += 1            

        if true == 1:
            total_t += 1
            correct_overlaps.append(overlap[3])
        else:
            if ((last_dict != None and ((int(overlap[0]) in last_dict["unmapped"]) or (int(overlap[1]) in last_dict["unmapped"]))) or
                (bwa_dict != None and ((int(overlap[0]) in bwa_dict["unmapped"]) or (int(overlap[1]) in bwa_dict["unmapped"]))) or
                (graphmap_dict != None and ((int(overlap[0]) in graphmap_dict["unmapped"]) or (int(overlap[1]) in graphmap_dict["unmapped"]))) or
                (joint_dict != None and ((int(overlap[0]) in joint_dict["unmapped"]) or (int(overlap[1]) in joint_dict["unmapped"])))):
                total_unknown += 1;
                unknown_overlaps.append(overlap[3]);
            else:
                total_f += 1
                faulty_overlaps.append(overlap[3])

    print ("Out path: %s" % (out_path));
    if (last_dict != None):
        precision = float(last_t) / (last_t + last_f);
        recall = last_t / float(last_dict["total"]);
        F1 = (2 * precision * recall) / (precision + recall);
        print("Last (T,F,Unknown(#),Prec(%%),Rec(%%),F1(%%)): %d, %d, %d, %.2f, %.2f, %.2f" % (last_t, last_f, last_unknown, precision*100.0, recall*100.0, F1*100.0))
    if (bwa_dict != None):
        precision = float(bwa_t) / (bwa_t + bwa_f);
        recall = bwa_t / float(bwa_dict["total"]);
        F1 = (2 * precision * recall) / (precision + recall);
        print("Bwa (T,F,Unknown(#),Prec(%%),Rec(%%),F1(%%)): %d, %d, %d, %.2f, %.2f, %.2f" % (bwa_t, bwa_f, bwa_unknown, precision*100.0, recall*100.0, F1*100.0))
    if (graphmap_dict != None):
        precision = float(graphmap_t) / (graphmap_t + graphmap_f);
        recall = graphmap_t / float(graphmap_dict["total"]);
        F1 = (2 * precision * recall) / (precision + recall);
        print("Graphmap (T,F,Unknown(#),Prec(%%),Rec(%%),F1(%%)): %d, %d, %d, %.2f, %.2f, %.2f" % (graphmap_t, graphmap_f, graphmap_unknown, precision*100.0, recall*100.0, F1*100.0))
    if (joint_dict != None):
        precision = float(joint_t) / (joint_t + joint_f);
        recall = joint_t / float(joint_dict["total"]);
        F1 = (2 * precision * recall) / (precision + recall);
        print("Joint (T,F,Unknown(#),Prec(%%),Rec(%%),F1(%%)): %d, %d, %d, %.2f, %.2f, %.2f" % (joint_t, joint_f, joint_unknown, precision*100.0, recall*100.0, F1*100.0))

#     print("Total (T,F,Unknown): %d, %d, %d" % (total_t, total_f, total_unknown))

    with open(out_path + "_true.mhap", "w") as file:
        for overlap in correct_overlaps:
            file.write(overlap + '\n')
    with open(out_path + "_false.mhap", "w") as file:
        for overlap in faulty_overlaps:
            file.write(overlap + '\n')
    with open(out_path + "_unknown.mhap", "w") as file:
        for overlap in unknown_overlaps:
            file.write(overlap + '\n')

    if (joint_dict != None):
        if (csv_path == None):
            csv_path = out_path + '.csv';
        fp = open(csv_path, 'a');
        # fp.write('Overlaps\tTP\tFP\tUnknown\tPrecision\tRecall\tF1\n');
        fp.write('%s\t%d\t%d\t%d\t%f\t%f\t%f\t# Overlaps\tTP\tFP\tUnknown\tPrecision\tRecall\tF1\n' % (in_path, joint_t, joint_f, joint_unknown, precision*100.0, recall*100.0, F1*100.0));
        fp.close();

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
    "    -a  <out_csv_file>\n"
    "        (optional)\n"
    "        file in which results will be appended (not overwritten) in a tab-separated format\n"
    "    -h, --help\n"
    "        prints out the help")

if __name__ == "__main__":
    main()
