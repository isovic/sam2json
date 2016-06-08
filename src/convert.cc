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
#include <string>
#include <vector>
#include <map>

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

  fprintf (fp_out, "{");

  for (int64_t i=0; i<all_ctg_alns.size(); i++) {
    auto it = all_ctg_alns.find(ctg_names[i]);
    // Get alignments for current contig.
    std::vector<const SingleSequence *> &ctg_alns = it->second;
    std::vector<IntervalType> aln_intervals;
    aln_intervals.reserve(ctg_alns.size());
    LOG_ALL("Building the interval tree for sequence '%s'.\n", ctg_names[i].c_str());
    std::vector<int64_t> aln_ends;
    aln_ends.reserve(ctg_alns.size());
    for (int64_t j=0; j<ctg_alns.size(); j++) {
      int64_t aln_start = ctg_alns[j]->get_aln().get_pos() - 1;
      int64_t aln_end = aln_start + ctg_alns[j]->get_aln().GetReferenceLengthFromCigar() - 1;
      aln_ends.push_back(aln_end);
      aln_intervals.push_back(IntervalType(aln_start, aln_end, ctg_alns[j]->get_sequence_absolute_id()));
    }
    IntervalTreeOverlaps aln_interval_tree(aln_intervals);
    LOG_ALL("Interval tree built.\n");
    LOG_ALL("Finding overlaps.\n");

    for (int64_t j=0; j<ctg_alns.size(); j++) {
      std::vector<IntervalType> found_intervals;
      int64_t aln_start = ctg_alns[j]->get_aln().get_pos() - 1;
      int64_t aln_end = aln_ends[j];
      aln_interval_tree.findOverlapping(aln_start, aln_end, found_intervals);
      fprintf (fp_out, "\"%d\": [", ctg_alns[j]->get_sequence_absolute_id() + 1);
      for (int64_t k=0; k<found_intervals.size(); k++) {
        fprintf (fp_out, "%d", (found_intervals[k].value + 1));
        if ((k + 1) < found_intervals.size()) {
          fprintf (fp_out, ", ");
        }
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

  fprintf (fp_out, "}");
}
