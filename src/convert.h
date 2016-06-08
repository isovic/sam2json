/*
 * convert.h
 *
 *  Created on: Jun 9, 2016
 *      Author: isovic
 */

#ifndef SRC_CONVERT_H_
#define SRC_CONVERT_H_

#include <string>
#include <map>
#include "sequences/sequence_file.h"

void Convert(const SequenceFile &seqs_sam, const std::map<std::string, int64_t> &qname_to_id, FILE *fp_out);



#endif /* SRC_CONVERT_H_ */
