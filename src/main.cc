/*
 * main.cc
 *
 *  Created on: Jan 24, 2016
 *      Author: isovic
 */

#include <sequences/sequence_test.h>
#include <stdio.h>
#include "log_system/log_system.h"
#include <sstream>
#include "sequences/sequence_file.h"
#include "argparser.h"
#include "parameters.h"
#include "convert.h"
#include "utility/utility_general.h"

void RunTests() {
  TEST_CLASS_SEQUENCE_ALIGNMENT();
  exit(0);
}

int main(int argc, char* argv[]) {
  //  RunTests();

  bool help = false;
  ProgramParameters parameters;
  ArgumentParser argparser;
  argparser.AddArgument(&(parameters.reads_path), VALUE_TYPE_STRING, "f", "reads", "", "Reads in FASTA/FASTQ format.", 0, "Input/Output options");
  argparser.AddArgument(&(parameters.aln_path), VALUE_TYPE_STRING, "i", "sam", "", "Path to a SAM file with read-to-target overlaps.", 0, "Input/Output options");
  argparser.AddArgument(&(parameters.out_path), VALUE_TYPE_STRING, "o", "out", "", "Output JSON file containing true positive overlaps.", 0, "Input/Output options");

  argparser.AddArgument(&help, VALUE_TYPE_BOOL, "h", "help", "0", "View this help.", 0, "Other options");

  if (argc == 1) {
//    fprintf (stderr, "  %s [options] <reads.fastq> <overlaps.mhap> <raw_contigs.fasta> <out_consensus.fasta>\n\n", argv[0]);
    fprintf (stderr, "%s\n", argparser.VerboseUsage().c_str());
    exit(1);
  }

  // Process the command line arguments.
  argparser.ProcessArguments(argc, argv);
  // Store the command line arguments for later use.
  for (int32_t i=0; i<argc; i++) { parameters.cmd_arguments.push_back(argv[i]); }
  parameters.program_folder = parameters.cmd_arguments[0].substr(0, parameters.cmd_arguments[0].find_last_of("\\/"));
  parameters.program_bin = parameters.cmd_arguments[0].substr(parameters.cmd_arguments[0].find_last_of("\\/") + 1);

  if (parameters.aln_path == "") {
    fprintf (stderr, "ERROR: Please specify the path to the SAM file containing 'true positive' alignments.\n");
    exit(1);
  }
  if (parameters.reads_path == "") {
    fprintf (stderr, "ERROR: Please specify the path to the reads file. This file is needed to mark the ordinal numbers to reads.\n");
    exit(1);
  }
  if (parameters.out_path == "") {
    fprintf (stderr, "ERROR: Please specify the path to the output JSON file.\n");
    exit(1);
  }

  if (parameters.aln_path == parameters.out_path) {
    fprintf (stderr, "ERROR: Output path is the same as the input SAM path! This would overwrite the input file. I don't like the idea, and I don't wanna. Exiting.\n");
    exit(1);
  }

  if (parameters.reads_path == parameters.out_path) {
    fprintf (stderr, "ERROR: Output path is the same as the input reads path! This would overwrite the input file. I don't like the idea, and I don't wanna. Exiting.\n");
    exit(1);
  }

  if (parameters.verbose_level == 1) {
    LogSystem::GetInstance().LOG_VERBOSE_TYPE = LOG_VERBOSE_STD;
  } else if (parameters.verbose_level > 1) {
    LogSystem::GetInstance().LOG_VERBOSE_TYPE = LOG_VERBOSE_FULL | LOG_VERBOSE_STD;
  }

  // Set the verbose level for the execution of this program.
  LogSystem::GetInstance().SetProgramVerboseLevelFromInt(parameters.verbose_level);

  /// Check if help was triggered.
  if (argparser.GetArgumentByLongName("help")->is_set == true) {
    fprintf (stderr, "  %s [options] <raw> <aln> <temp>\n\n", argv[0]);
    fprintf (stderr, "%s\n", argparser.VerboseUsage().c_str());
    fflush(stderr);
    exit(1);
  }

  LOG_ALL("Hashing qnames from the reads file.\n");
  SequenceFile seqs_reads(SEQ_FORMAT_AUTO, parameters.reads_path);
  std::map<std::string, int64_t> qname_to_id;
  for (int64_t i=0; i<seqs_reads.get_sequences().size(); i++) {
    qname_to_id[seqs_reads.get_sequences()[i]->get_header()] = i;
    qname_to_id[TrimToFirstSpace(seqs_reads.get_sequences()[i]->get_header())] = i;
  }
  seqs_reads.Clear();

  LOG_ALL("Reading the SAM file.\n");
  FILE *fp = fopen(parameters.out_path.c_str(), "w");
  SequenceFile seqs_sam(SEQ_FORMAT_AUTO, parameters.aln_path);
  Convert(seqs_sam, qname_to_id, fp);
  fclose(fp);

	return 0;
}
