/*
 * parameters.h
 *
 *  Created on: Feb 23, 2016
 *      Author: isovic
 */

#ifndef SRC_RACON_PARAMETERR_H_
#define SRC_RACON_PARAMETERR_H_

#include <string>


struct ProgramParameters {
  std::string aln_path = "";
  std::string reads_path = "";
  std::string out_path = "";
  int32_t verbose_level = 1;

  std::string program_bin;
  std::string program_folder;
  std::vector<std::string> cmd_arguments;
};

#endif /* SRC_PARAMETERS_H_ */
