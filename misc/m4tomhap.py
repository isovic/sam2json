#! /usr/bin/python

import os;
import sys;

import numpy as np;

def peek(fp, num_chars):
	data = fp.read(num_chars);
	if len(data) == 0:
		return '';
	fp.seek(num_chars * -1, 1);
	return data;

def get_single_read(fp):
	lines = [];
	
	line = fp.readline();
	header = line.rstrip();
	header_leading_char = '';
	if (len(header) > 0):
		sequence_separator = header[0];
		header_leading_char = header[0];
		header = header[1:];			# Strip the '>' or '@' sign from the beginning.
	else:
		return ['', []];
	
	if (header_leading_char == '>'):
		num_expected_lines = 2;
	elif (header_leading_char == '@'):
		num_expected_lines = 4;
	else:
		sys.stderr.write('ERROR: Sequence is not in FASTA nor FASTQ format! Leading character in the header is "%s". Exiting.\n' % (header_leading_char));
		exit(1);

	next_char = peek(fp, 1);
	num_loaded_lines = 1;
	
	line_string = '';
	lines.append(header_leading_char + header);

	num_lines = 1;
	while (num_loaded_lines < num_expected_lines and len(next_char) > 0):
		line = fp.readline().strip();
		next_char = peek(fp, 1);

		if (header_leading_char == '@'):
			if ((num_loaded_lines == 1 and next_char == '+') or
				(num_loaded_lines == 2 and line[0] == '+') or
				(num_loaded_lines == 3 and next_char == sequence_separator)):
					line_string += line.rstrip();
					lines.append(line_string);
					num_loaded_lines += 1;
					line_string = '';
			elif (num_loaded_lines == 2 and line[0] != '+'):
				sys.stderr.write('ERROR: File is not in FASTQ format! Separator between seq and qual is not "+" but "%s". Exiting.\n' % (line[0]));
				exit(1);
			else:
				line_string += line.rstrip();

		elif (header_leading_char == '>'):
			if (num_loaded_lines == 1 and next_char == sequence_separator):
				line_string += line.rstrip();
				lines.append(line_string);
				num_loaded_lines = 2;
				line_string = '';
			else:
				line_string += line.rstrip();

		num_lines += 1;
	if (line_string != ''):
		lines.append(line_string);
		num_loaded_lines += 1;

	return [header, lines];

def get_headers_and_lengths(fastq_path):
	headers = [];
	lengths = [];
	fp_in = None;
	try:
		fp_in = open(fastq_path, 'r');
	except IOError:
		print 'ERROR: Could not open file "%s" for reading!' % fastq_path;
		exit(1);
	seq_id = 0;
	while True:
		[header, read] = get_single_read(fp_in);
		if (len(header) == 0):
			break;
		headers.append(header);
		lengths.append(len(read[1]));
		seq_id += 1;
	fp_in.close();
	return [headers, lengths];

def convert_line(qname_hash, m4_line):
	sl = m4_line.split();
	qname = sl[0].split('/')[0];
	tname = sl[1];
	try:   
	        id1 = str(qname_hash[qname]);
	except Exception, e:
	        sys.stderr.write('(id1) Qname %s not found!' % (qname));
	        sys.stderr.write(str(e));
	        sys.stderr.write('Line:\n%s\n' % (m4_line));
	        sys.stderr.write(str(sl));
	        exit(1);
	try:
	        id2 = str(qname_hash[tname]);
	except Exception, e:
	        sys.stderr.write('(id2) Tname %s not found!' % (tname));
	        sys.stderr.write(str(e));
	        sys.stderr.write('Line:\n%s\n' % (m4_line));
	        sys.stderr.write(str(sl));
	        exit(1);

	mhap_line = ' '.join([id1, id2] + sl[2:-1]);
	return mhap_line;

def convert(in_reads, in_m4):
	[headers, lengths] = get_headers_and_lengths(in_reads);
	qname_hash = {};
	for i in xrange(0, len(headers)):
		qname_hash[headers[i]] = (i + 1);
		qname_hash[headers[i].split()[0]] = (i + 1);
		qname_hash[headers[i].split('/')[0]] = (i + 1);

	try:
		fp = open(in_m4, 'r');
	except:
		sys.stderr.write('ERROR: Could not open file "%s" for reading! Exiting.\n' % (in_m4));
		exit(1);

	for line in fp:
		mhap_line = convert_line(qname_hash, line.strip());
		print mhap_line;

	fp.close();

def main():
	if (len(sys.argv) != 3):
		sys.stderr.write('Usage:\n');
		sys.stderr.write('\t%s <reads.fastq> <in.m4>' % (sys.argv[0]));
		sys.stderr.write('\n');
		sys.stderr.write('Output is to STDOUT.\n');
		sys.stderr.write('\n');
		exit(1);

	in_reads = sys.argv[1];
	in_m4 = sys.argv[2];
	convert(in_reads, in_m4);

if __name__ == "__main__":
	main();
