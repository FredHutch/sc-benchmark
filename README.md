sc-benchmark
============

Scientific Computing benchmarks (HPC, storage, genomics)


scratch-dna.py
--------------

    user@box:$ ~/py/scratch-dna.py
    Error! 4 arguments required. 
    Execute scratch-dna.py [number-of-files] [file-size-bytes]  [random-file-size-multiplier] [writable-directory]

scratch-dna.py is a storage benchmarking tool that creates a random DNA string, concatenates this string a random number of times and writes the result multiple files with varying length. 

2 examples: 

    user@box:$ ~/py/scratch-dna.py 1000 2000 3000 .
    box: ... building random DNA sequence of 1.953 KB...
    box: ... writing 1000 files with filesizes between 1.953 KB and 5,859.375 KB ...
    box: 2897.315644 MB written in 8.609 seconds (336.559 MB/s, 116 files/s)

here we are writing 1000 files into the current directory. The files contain a dna snippet that is 2000 bytes long and each snippet is contatenated with the running file counter and the current hostname and then duplicated n times (n is a random number between 1 and 3000).

    user@box:$ ~/py/scratch-dna.py 10000 4 1 .
    box: ... building random DNA sequence of 0.004 KB...
    box: ... writing 10000 files with filesizes between 0.004 KB and 0.004 KB ...
    box: 0.141993 MB written in 20.721 seconds (0.007 MB/s, 482 files/s)
    
    box:$ cat box/scr-box-file-6985-1
    6985CATCbox

here we are writing 10000 small files (max 12 bytes) into the current directory. The dna snippet is 4 bytes long and is not duplicated.

In general dna snippet would be much more random if it could be regenerated for each file, however this would increase compute times. If we run this scratch-dna.py on a compute cluster each node would generate unique data.

