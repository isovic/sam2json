# sam2json
This tool takes in a SAM file of read to reference alignments, and finds overlaps and stores them to a JSON format for easy parsing in Python. Intended for evaluating overlaps.

## Install  
```
https://github.com/isovic/sam2json.git & make modules & make  
```

## Output  
Output JSON file contains a dictionary of pairs:
- key - ID of a read for which a list of overlapping reads is given,  
- value - an array of IDs of reads with which the key read has an overlap with.  
