# sam2json
This tool takes in a SAM file of read to reference alignments, and finds overlaps and stores them to a JSON format for easy parsing in Python. Intended for evaluating overlaps.

## Install  
```
https://github.com/isovic/sam2json.git & make modules & make  
```

## Usage
To create JSON file for overlap evaluation, run:  
```  
bin/sam2json -f reads.fastq -i reads.sam -o reads.json  
```  

To evaluate a MHAP file of overlaps ```overlaps.mhap``` against a pre-calculated truths JSON file ```reads.json```, run:  
```  
./eval-mhap.py -j reads.json -i overlaps.mhap -o overlaps.eval  
```  

Alignments can be generated using multiple aligners, e.g. GraphMap, BWA-MEM and LAST:  
```  
bin/sam2json -f reads.fastq -i graphmap.sam -o graphmap.json  
bin/sam2json -f reads.fastq -i bwamem.sam -o bwamem.json  
bin/sam2json -f reads.fastq -i last.sam -o last.json  
```  

An overlap file can then be evaluated against all three at the same time:  
```  
./eval-mhap.py -g graphmap.json -b bwamem.json -l last.json -i overlaps.mhap -o overlaps.eval  
```  

## JSON format  
JSON file contains a dictionary of pairs:
- key - ID of a read for which a list of overlapping reads is given,  
- value - an array of IDs of reads with which the key read has an overlap with.  
