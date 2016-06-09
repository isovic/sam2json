/*
 * convert.cc
 *
 *  Created on: Jun 9, 2016
 *      Author: isovic
 */

#include "intervaltree/IntervalTree.h"
#include "log_system/log_system.h"
#include "sequences/sequence_file.h"
#include "sequences/single_sequence.h"
#include "utility/utility_general.h"
#include <string>
#include <vector>
#include <map>
#include <algorithm>

typedef Interval<int64_t> IntervalType;
typedef IntervalTree<int64_t> IntervalTreeOverlaps;

int GroupAlignmentsToContigs(const SequenceFile &alns, std::vector<std::string> &ctg_names, std::map<std::string, std::vector<const SingleSequence *> > &ctg_alns) {
  ctg_names.clear();
  ctg_alns.clear();

  for (int64_t i=0; i<alns.get_sequences().size(); i++) {
    if (alns.get_sequences()[i]->get_aln().IsMapped() == false) continue;

    auto it = ctg_alns.find(alns.get_sequences()[i]->get_aln().get_rname());
    if (it != ctg_alns.end()) {
      it->second.push_back((const SingleSequence *) (alns.get_sequences()[i]));
    } else {
      ctg_alns[alns.get_sequences()[i]->get_aln().get_rname()] = std::vector<const SingleSequence *> {(const SingleSequence *) alns.get_sequences()[i]};
      ctg_names.push_back(alns.get_sequences()[i]->get_aln().get_rname());
    }
  }

  return 0;
}

void Convert(const SequenceFile &seqs_sam, const std::map<std::string, int64_t> &qname_to_id, FILE *fp_out) {
  std::map<std::string, std::vector<SingleSequence *>> ctg_alns;

  std::vector<std::string> ctg_names;
  std::map<std::string, std::vector<const SingleSequence *> > all_ctg_alns;
  GroupAlignmentsToContigs(seqs_sam, ctg_names, all_ctg_alns);

  int64_t num_seqs = 0;
  int64_t total = 0;
  fprintf (fp_out, "{");

  for (int64_t i=0; i<all_ctg_alns.size(); i++) {
    auto it = all_ctg_alns.find(ctg_names[i]);
    // Get alignments for current contig.
    std::vector<const SingleSequence *> &ctg_alns = it->second;
    std::vector<IntervalType> aln_intervals;
    aln_intervals.reserve(ctg_alns.size());
    LOG_ALL("Building the interval tree for sequence '%s'.\n", ctg_names[i].c_str());
    // Memoize the alignment ends so we don't have to recalculate them based on CIGAR strings.
    std::vector<int64_t> aln_ends;
    aln_ends.reserve(ctg_alns.size());
    // Qnames need to be converted to IDs.
    std::vector<std::string> aln_headers;
    aln_headers.reserve(ctg_alns.size());
    // Create an array of intervals to initialize the IntervalTree. Also, initialize the proper Qnames for MHAP format.
    for (int64_t j=0; j<ctg_alns.size(); j++) {
      num_seqs += 1;
      int64_t aln_start = ctg_alns[j]->get_aln().get_pos() - 1;
      int64_t aln_end = aln_start + ctg_alns[j]->get_aln().GetReferenceLengthFromCigar() - 1;
      aln_ends.push_back(aln_end);
      aln_intervals.push_back(IntervalType(aln_start, aln_end, j));
      std::string header = ctg_alns[j]->get_header();
      aln_headers.push_back(FormatString("%ld", (qname_to_id.find(header)->second + 1)));

//      if ((qname_to_id.find(header)->second + 1) == 1 || (qname_to_id.find(header)->second + 1) == 137) {
//        printf ("(qname_to_id.find(header)->second + 1) = %ld\n", (qname_to_id.find(header)->second + 1));
////        ctg_alns[j]->Verbose(stdout);
//        printf ("%s\n", ctg_alns[j]->MakeSAMLine().c_str());
//      }
    }
    IntervalTreeOverlaps aln_interval_tree(aln_intervals);
    LOG_ALL("Interval tree built.\n");
    LOG_ALL("Finding overlaps.\n");

    for (int64_t j=0; j<ctg_alns.size(); j++) {
      std::vector<IntervalType> found_intervals;
      // Get the start and end positions for the current sequence.
      int64_t aln_start = ctg_alns[j]->get_aln().get_pos() - 1;
      int64_t aln_end = aln_ends[j];
      aln_interval_tree.findOverlapping(aln_start, aln_end, found_intervals);
      // Not necessarily required to sort, but let's be thorough.
      std::sort(found_intervals.begin(), found_intervals.end(), [](const IntervalType &a, const IntervalType &b) { return a.value < b.value; } );
      // Total count of overlaps. In the end it will probably be double the edge count.
      total += found_intervals.size();

      // Write the output in JSON format.
      bool previously_written = false;
      fprintf (fp_out, "\"%s\": [", aln_headers[j].c_str());
      for (int64_t k=0; k<found_intervals.size(); k++) {
        if (found_intervals[k].value == j) { continue; }
        if (k > 0 && previously_written == true) {
          fprintf (fp_out, ", ");
        }
        fprintf (fp_out, "%s", (aln_headers[found_intervals[k].value].c_str()));
        previously_written = true;
      }
      fprintf (fp_out, "]");

      if ((j + 1) < ctg_alns.size()) {
        fprintf (fp_out, ", ");
      }
    }

    if ((i + 1) < all_ctg_alns.size()) {
      fprintf (fp_out, ", ");
    }

    LOG_ALL("Finished generating overlaps.\n");
    LOG_NEWLINE;
  }

  // Do not count edges twice, as well as self overlaps.
  fprintf (fp_out, ", \"total\": %ld}", (total/2 - num_seqs));
}
