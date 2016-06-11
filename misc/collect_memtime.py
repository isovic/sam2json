#! /usr/bin/python

import os;
import sys;
import fnmatch;
import subprocess;
from time import gmtime, strftime

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__));

# Finds all files with a given filename pattern starting from the given path, recursivelly.
def find_files(start_path, file_pattern, max_depth=-1):
	matches = []
	for root, dirnames, filenames in os.walk(start_path):
		for filename in fnmatch.filter(filenames, file_pattern):
			depth = len(root.split('/'))
			if (max_depth < 0 or (max_depth >= 0 and depth <= max_depth)):
				matches.append(os.path.join(root, filename))

	matches.sort()
	return matches

def parse_memtime(memtime_path):
	cmdline = '';
	realtime = 0;
	cputime = 0;
	usertime = 0;
	systemtime = 0;
	maxrss = 0;
	rsscache = 0;
	time_unit = '';
	mem_unit = '';

	try:
		fp = open(memtime_path, 'r');
		lines = [line.strip() for line in fp.readlines() if (len(line.strip()) > 0)];
		fp.close();
	except Exception, e:
		# sys.stderr.write('ERROR: Could not find memory and time statistics in file "%s".\n' % (memtime_path));
		return [cmdline, realtime, cputime, usertime, systemtime, maxrss, time_unit, mem_unit];

	for line in lines:
		if (len(line.strip().split(':')) != 2):
			continue;

		if (line.startswith('Command line:')):
			cmdline = line.split(':')[1].strip();
		elif (line.startswith('Real time:')):
			split_line = line.split(':')[1].strip().split(' ');
			realtime = float(split_line[0].strip());
			try:
				time_unit = split_line[1].strip();
			except:
				sys.stderr.write('ERROR: No time unit specified in line: "%s"! Exiting.\n' % (line.strip()));
				exit(1);
		elif (line.startswith('CPU time:')):
			split_line = line.split(':')[1].strip().split(' ');
			cputime = float(split_line[0].strip());
			try:
				time_unit = split_line[1].strip();
			except:
				sys.stderr.write('ERROR: No time unit specified in line: "%s"! Exiting.\n' % (line.strip()));
				exit(1);
		elif (line.startswith('User time:')):
			split_line = line.split(':')[1].strip().split(' ');
			usertime = float(split_line[0].strip());
			try:
				time_unit = split_line[1].strip();
			except:
				sys.stderr.write('ERROR: No time unit specified in line: "%s"! Exiting.\n' % (line.strip()));
				exit(1);
		elif (line.startswith('System time:')):
			split_line = line.split(':')[1].strip().split(' ');
			systemtime = float(split_line[0].strip());
			try:
				time_unit = split_line[1].strip();
			except:
				sys.stderr.write('ERROR: No time unit specified in line: "%s"! Exiting.\n' % (line.strip()));
				exit(1);
		elif (line.startswith('Maximum RSS:')):
			split_line = line.split(':')[1].strip().split(' ');
			maxrss = float(split_line[0].strip());
			try:
				mem_unit = split_line[1].strip();
			except:
				sys.stderr.write('ERROR: No memory unit specified in line: "%s"! Exiting.\n' % (line.strip()));
				exit(1);
		# elif (line.startswith('')):
		# 	split_line = line.split(':')[1].strip().split(' ');
		# 	rsscache = float(split_line[0].strip());
		# 	mem_unit = split_line[1].strip();
	if (cputime <= 0.0):
		cputime = usertime + systemtime;

	return [cmdline, realtime, cputime, usertime, systemtime, maxrss, time_unit, mem_unit];

def parse_memtime_files_and_accumulate(memtime_files, final_memtime_file):
	final_command_line = '';
	final_real_time = 0.0;
	final_cpu_time = 0.0;
	final_user_time = 0.0;
	final_system_time = 0.0;
	final_time_unit = 's';
	final_max_rss = 0;
	final_mem_unit = 'MB';

	i = 0;
	for memtime_file in memtime_files:
		i += 1;
		sys.stderr.write('Parsing memtime file "%s"...\n' % (memtime_file));

		[cmdline, realtime, cputime, usertime, systemtime, maxrss, time_unit, mem_unit] = parse_memtime(memtime_file);
		if (i == 1):
			final_command_line = cmdline;
			final_real_time = realtime;
			final_cpu_time = cputime;
			final_user_time = usertime;
			final_system_time = systemtime;
			final_max_rss += maxrss;
			final_time_unit = time_unit;
			final_mem_unit = mem_unit;
		else:
			if (time_unit == final_time_unit and mem_unit == final_mem_unit):
				final_command_line += '; ' + cmdline;
				final_real_time += realtime;
				final_cpu_time += cputime;
				final_user_time += usertime;
				final_system_time += systemtime;
				# final_max_rss += maxrss;
				final_max_rss = max(final_max_rss, maxrss);
			else:
				sys.stderr.write('Memory or time units not the same in all files! Instead of handling this, we decided to be lazy and just give up.\n');
				break;

	try:
		fp = open(final_memtime_file, 'w');
		sys.stderr.write('Writing the total memtime stats file to: "%s".\n' % (final_memtime_file));
	except Exception, e:
		sys.stderr.write('ERROR: Could not open file "%s" for writing!\n' % (final_memtime_file));
		return;

	if (final_cpu_time <= 0.0):
		final_cpu_time = final_user_time + final_system_time;

	fp.write('Command line: %s\n' % (final_command_line));
	fp.write('Real time: %f %s\n' % (final_real_time, final_time_unit));
	fp.write('CPU time: %f %s\n' % (final_cpu_time, final_time_unit));
	fp.write('User time: %f %s\n' % (final_user_time, final_time_unit));
	fp.write('System time: %f %s\n' % (final_system_time, final_time_unit));
	fp.write('Maximum RSS: %f %s\n' % (final_max_rss, final_mem_unit));

	fp.close();

def parse_memtime_folder_and_accumulate(memtime_folder, final_memtime_file):
		memtime_files = [value for value in find_files(memtime_folder, '*.memtime') if (value.endswith('total.memtime') == False)];
		sys.stderr.write('Collecting memtime stats from folder "%s":\n' % (memtime_folder));
		parse_memtime_files_and_accumulate(memtime_files, final_memtime_file);
		sys.stderr.write('\n');

def autocollect_memtimes(results_path):
	all_memtime_files = [value for value in find_files(results_path, '*.memtime') if (value.endswith('total.memtime') == False)];
	all_memtime_folders = sorted(set([os.path.dirname(value) for value in all_memtime_files]));

	i = 0;
	for memtime_folder in all_memtime_folders:
		i += 1;
		memtime_files = [value for value in find_files(memtime_folder, '*.memtime') if (value.endswith('total.memtime') == False)];
		memtime_summary_basename = memtime_folder.split(results_path)[-1];
		memtime_summary_basename = memtime_summary_basename if memtime_summary_basename[0] != '/' else memtime_summary_basename[1:];
		memtime_summary_basename = memtime_summary_basename.replace('/', '_');
		memtime_summary_path = '%s/total.memtime' % (memtime_folder, memtime_summary_basename);

		sys.stderr.write('[%d] Collecting memtime stats from folder "%s":\n' % (i, memtime_folder));
		parse_memtime_files_and_accumulate(memtime_files, memtime_summary_path);
		sys.stderr.write('\n');


def convert_memory_to_bytes(memory_value, memory_unit):
	memory_unit_lower = memory_unit.lower();
	if (memory_unit_lower == 'b'):
		return (memory_value + 0);
	elif (memory_unit_lower == 'kb' or memory_unit_lower == 'k'):
		return (memory_value * 1024.0);
	elif (memory_unit_lower == 'mb' or memory_unit_lower == 'm'):
		return (memory_value * 1024.0 * 1024.0);
	elif (memory_unit_lower == 'gb' or memory_unit_lower == 'g'):
		return (memory_value * 1024.0 * 1024.0 * 1024.0);
	elif (memory_unit_lower == 'tb' or memory_unit_lower == 't'):
		return (memory_value * 1024.0 * 1024.0 * 1024.0 * 1024.0);
	return memory_value;

def convert_memory_from_bytes(memory_value, target_memory_unit):
	memory_unit_lower = target_memory_unit.lower();
	if (memory_unit_lower == 'b'):
		return (memory_value + 0);
	elif (memory_unit_lower == 'kb' or memory_unit_lower == 'k'):
		return (memory_value / 1024.0);
	elif (memory_unit_lower == 'mb' or memory_unit_lower == 'm'):
		return (memory_value / (1024.0 * 1024.0));
	elif (memory_unit_lower == 'gb' or memory_unit_lower == 'g'):
		return (memory_value / (1024.0 * 1024.0 * 1024.0));
	elif (memory_unit_lower == 'tb' or memory_unit_lower == 't'):
		return (memory_value / (1024.0 * 1024.0 * 1024.0 * 1024.0));
	return memory_value;

def convert_memory_units(memory_value, memory_unit, target_unit):
	byte_value = convert_memory_to_bytes(memory_value, memory_unit);
	ret_value = convert_memory_from_bytes(byte_value, target_unit);
	return ret_value;


def convert_time_to_seconds(time_value, time_unit):
	time_unit_lower = time_unit.lower();
	if (time_unit_lower == 's'):
		return (time_value + 0.0);
	elif (time_unit_lower == 'min'):
		return (time_value * 60.0);
	elif (time_unit_lower == 'h'):
		return (time_value * (60.0 * 60.0));
	elif (time_unit_lower == 'd'):
		return (time_value * (60.0 * 60.0 * 24.0));
	return time_value;

def convert_time_from_seconds(time_value, time_unit):
	time_unit_lower = time_unit.lower();
	if (time_unit_lower == 's'):
		return (time_value + 0.0);
	elif (time_unit_lower == 'min'):
		return (time_value / 60.0);
	elif (time_unit_lower == 'h'):
		return (time_value / (60.0 * 60.0));
	elif (time_unit_lower == 'd'):
		return (time_value / (60.0 * 60.0 * 24.0));
	return time_value;

def convert_time_units(time_value, time_unit, target_time_unit):
	sec_value = convert_time_to_seconds(time_value, time_unit);
	ret_value = convert_time_from_seconds(sec_value, target_time_unit);
	return ret_value;



def summarize_memtimes(results_path, out_summary_file):
	fp_out = sys.stdout;
	try:
		fp_out = open(out_summary_file, 'w');
	except:
		sys.stderr.write('ERROR: Could not open file "%s" for writing! Using STDOUT instead.\n' % (out_summary_file));

	csv_line = 'Dataset; Assembler; Real time [min]; CPU time [min]; Max. RSS [MB]';
	fp_out.write(csv_line + '\n');

	memtime_files = find_files(results_path, '*total.memtime');
	for memtime_file in memtime_files:
		memtime_folder = os.path.dirname(memtime_file);
		dataset_name = memtime_folder.split(results_path)[-1];
		dataset_name = dataset_name if dataset_name[0] != '/' else dataset_name[1:];
		dataset_name = dataset_name.replace('/', '; ');

		### [cmdline, realtime, cputime, usertime, systemtime, maxrss, time_unit, mem_unit]
		[cmdline, realtime, cputime, usertime, systemtime, maxrss, time_unit, mem_unit] = parse_memtime(memtime_file);

		if (time_unit == 's'):
			realtime /= 60.0;
			cputime /= 60.0;
			usertime /= 60.0;
			systemtime /= 60.0;

		maxrss = convert_memory_units(maxrss, mem_unit, 'MB');

		csv_line = '%s; %.2f; %.2f; %.2f' % (dataset_name, realtime, cputime, maxrss);
		fp_out.write(csv_line + '\n');

	if (fp_out != sys.stdout):
		fp_out.close();

def parse_memtime_report(report_file, parameters, target_time_unit, target_mem_unit):
	memtime_stats = parse_memtime(report_file);
	if (memtime_stats == None):
		return ['-' for value in parameters];

	[cmdline, realtime, cputime, usertime, systemtime, maxrss, time_unit, mem_unit] = memtime_stats;

	results = [];
	for parameter in parameters:
		if (parameter == 'Command line'):
			cmdline = str(convert_time_units(float(cmdline), time_unit, target_time_unit));
			results.append(cmdline);
		elif (parameter == 'Real time'):
			realtime = str(convert_time_units(float(realtime), time_unit, target_time_unit));
			results.append(realtime);
		elif (parameter == 'CPU time'):
			cputime = str(convert_time_units(float(cputime), time_unit, target_time_unit));
			results.append(cputime);
		elif (parameter == 'User time'):
			usertime = str(convert_time_units(float(usertime), time_unit, target_time_unit));
			results.append(usertime);
		elif (parameter == 'System time'):
			systemtime = str(convert_time_units(float(systemtime), time_unit, target_time_unit));
			results.append(systemtime);
		elif (parameter == 'Maximum RSS'):
			maxrss = str(convert_memory_units(float(maxrss), mem_unit, target_mem_unit));
			results.append(maxrss);
	return results;

def execute_command(command):
	sys.stderr.write('[Executing] "%s"\n' % (command));
	subprocess.call(command, shell=True);
	sys.stderr.write('\n');

if __name__ == "__main__":
	if (len(sys.argv) != 5):
		sys.stderr.write('Tool to collect all memtime results recursivelly for a given folder.\n');
		sys.stderr.write('\n');
		sys.stderr.write('Usage:\n');
		sys.stderr.write('\t%s <root_folder> <out.csv> time_unit mem_unit\n' % (sys.argv[0]));
		sys.stderr.write('\n');
		sys.stderr.write('time_unit: s, min, h, d\n');
		sys.stderr.write('mem unit:  b, kb, mb, gb, tb\n')
		sys.stderr.write('\n');
		exit(1);

	memtime_folder = sys.argv[1];
	out_collect_file = sys.argv[2];
	target_time_unit = sys.argv[3];
	target_mem_unit = sys.argv[4];

	if (not target_mem_unit in ['b', 'kb', 'mb', 'gb', 'tb']):
		sys.stderr.write('ERROR: Unknown memory unit "%s"! Exiting.\n' % (target_mem_unit));
		exit(1);
	if (not target_time_unit in ['s', 'min', 'h', 'd']):
		sys.stderr.write('ERROR: Unknown time unit "%s"! Exiting.\n' % (target_time_unit));
		exit(1);

	try:
		fp_out = open(out_collect_file, 'w');
	except:
		sys.stderr.write('ERROR: Could not open file "%s" for writing! Exiting.\n' % (out_collect_file));
		exit(1);

	# timestamp = strftime("%Y%m%d_%H%M%S", gmtime());

	memtime_files = [value for value in find_files(memtime_folder, '*.memtime')];
	sys.stderr.write('Collecting memtime stats from folder "%s":\n' % (memtime_folder));
	fp_out.write('memtime_file\tcmdline\trealtime\tcputime\tusertime\tsystemtime\tmaxrss\ttime_unit\tmem_unit\n');

	for i in xrange(0, len(memtime_files)):
		memtime_file = memtime_files[i];
		sys.stderr.write('Parsing memtime file "%s"...\n' % (memtime_file));
		memtime_results = parse_memtime(memtime_file);
		[cmdline, realtime, cputime, usertime, systemtime, maxrss, time_unit, mem_unit] = memtime_results;
		# fp_out.write('%s\t%s\n' % (memtime_file, '\t'.join([str(val) for val in memtime_results])));
		realtime = '%.2f' % (convert_time_units(float(realtime), time_unit, target_time_unit));
		cputime = '%.2f' % (convert_time_units(float(cputime), time_unit, target_time_unit));
		usertime = '%.2f' % (convert_time_units(float(usertime), time_unit, target_time_unit));
		systemtime = '%.2f' % (convert_time_units(float(systemtime), time_unit, target_time_unit));
		maxrss = '%.2f' % (convert_memory_units(float(maxrss), mem_unit, target_mem_unit));
		fp_out.write('%s\t%s\n' % (memtime_file, '\t'.join([val for val in [realtime, cputime, usertime, systemtime, maxrss, target_time_unit, target_mem_unit, cmdline]])));
