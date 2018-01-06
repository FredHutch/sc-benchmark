# sc-benchmark


Scientific Computing benchmarks (HPC, storage, genomics)

## Compute


### rbenchmark

using a slightly modified version of this code :
https://www.rdocumentation.org/packages/rbenchmark/versions/1.0.0/topics/benchmark

We ran tests using R 3.3.2 on Ubuntu 14.04 after AWS had patched for the
meltdown vulnerability. 22 sec local vs 25 sec on AWS suggests the impact of the
meltdown patches on CPU intensive workflows such as statistical simulations is relatively small.
The AWS instance has ca 7% better Passmark benchmarks (measured before the
patching) despite clocking a bit lower according to https://www.cpubenchmark.net/.
This suggests that AWS is overclocking their CPUs.

#### 25 sec on a AWS C4 instance (E5-2666 v3 @ 2.90GHz - CPU Mark 24877):

    test replications elapsed relative user.self sys.self user.child sys.child
    1 1:10^6          100   0.106        1     0.074    0.032          0         0
                    test elapsed replications
    1 random.array(100, 100)   0.811         1000
    2 random.array(100, 100)   0.805         1000
    3 random.array(100, 100)   0.805         1000
    4 random.array(100, 100)   0.817         1000
    5 random.array(100, 100)   0.808         1000
    6 random.array(100, 100)   0.805         1000
    test replications elapsed  average
    2  arr           10   0.008 0.000800
    4  arr          100   0.080 0.000800
    6  arr         1000   0.797 0.000797
    1  rep           10   0.085 0.008500
    3  rep          100   0.846 0.008460
    5  rep         1000   8.601 0.008601
    test elapsed replications
    2  arr   0.803         1000
    1  rep   8.585         1000

    real	0m25.01s
    user	0m0.78s
    sys	  0m0.32s

#### 22 sec on local hardware (E5-2667 v3 @ 3.20GHz - CPU Mark 23207)

    $ time ./rbenchmark.R
        test replications elapsed relative user.self sys.self user.child sys.child
    1 1:10^6          100   0.133        1     0.044    0.089          0         0
                        test elapsed replications
    1 random.array(100, 100)   0.780         1000
    2 random.array(100, 100)   0.685         1000
    3 random.array(100, 100)   0.687         1000
    4 random.array(100, 100)   0.695         1000
    5 random.array(100, 100)   0.685         1000
    6 random.array(100, 100)   0.687         1000
      test replications elapsed  average
    2  arr           10   0.007 0.000700
    4  arr          100   0.069 0.000690
    6  arr         1000   0.677 0.000677
    1  rep           10   0.074 0.007400
    3  rep          100   0.729 0.007290
    5  rep         1000   7.320 0.007320
      test elapsed replications
    2  arr   0.683         1000
    1  rep   7.294         1000

    real	0m21.827s
    user	0m21.319s
    sys	0m0.314s



### Storage

### scratch-dna.py

    user@box:$ ~/py/scratch-dna.py
    Error! 4 arguments required.
    Execute scratch-dna.py [number-of-files] [file-size-bytes]  [random-file-size-multiplier] [writable-directory]

scratch-dna.py is a storage benchmarking tool that creates a random DNA string, concatenates this string a random number of times and writes the result multiple files with varying length.

2 examples:

    user@box:$ ~/py/scratch-dna.py 1000 2000 3000 .
    box: ... building random DNA sequence of 1.953 KB...
    box: ... writing 1000 files with filesizes between 1.953 KB and 5,859.375 KB ...
    box: 2897.315644 MB written in 8.609 seconds (336.559 MB/s, 116 files/s)

here we are writing 1000 files into the current directory to evaluate throughput performance. The files contain a dna snippet that is 2000 bytes long and each snippet is contatenated with the running file counter and the current hostname and then duplicated n times (n is a random number between 1 and 3000).

    user@box:$ ~/py/scratch-dna.py 10000 4 1 .
    box: ... building random DNA sequence of 0.004 KB...
    box: ... writing 10000 files with filesizes between 0.004 KB and 0.004 KB ...
    box: 0.141993 MB written in 20.721 seconds (0.007 MB/s, 482 files/s)

    box:$ cat box/scr-box-file-6985-1
    6985CATCbox

here we are writing 10000 small files (max 12 bytes) into the current directory to evaluate metadata performance. The dna snippet is 4 bytes long and is not duplicated.

In general dna snippet would be much more random if it could be regenerated for each file, however this would increase compute times. If we run this scratch-dna.py on a compute cluster each node would generate unique data.

scatch-dna-go
-------------

A drop in replacement for scratch-dna.py written in Go that adds the ability to specify how many files to write in parallel (-p num). Also adds verbose output (-v) that shows progress as files are being written.

### Example 1 - single threaded:

```
./scratch-dna-go 1000 1048576 10 ~/dna
Building random DNA sequence of 1.0 MB...

Writing 1000 files with filesizes between 1.0 MB and 10.0 MB...


Done!
Number of Files Written: 1000, Total Size: 5.4GiB, Avg FPS: 34, Avg Throughput: 190 MiB/s, Elapsed Time: 29 seconds
```

### Example 2 - 8 threads with verbose output:

```
./scratch-dna-go -v -p 8 1000 1048576 10 ~/dna
Building random DNA sequence of 1.0 MB...

Writing 1000 files with filesizes between 1.0 MB and 10.0 MB...

Files Completed:     139, Data Written:   0.7GiB, Files Remaining:     868, Cur FPS:   139, Throughput:  745 MiB/s
Files Completed:     277, Data Written:   1.4GiB, Files Remaining:     730, Cur FPS:   138, Throughput:  738 MiB/s
Files Completed:     354, Data Written:   1.8GiB, Files Remaining:     652, Cur FPS:   118, Throughput:  626 MiB/s
Files Completed:     370, Data Written:   1.9GiB, Files Remaining:     635, Cur FPS:    92, Throughput:  494 MiB/s
Files Completed:     428, Data Written:   2.2GiB, Files Remaining:     578, Cur FPS:    85, Throughput:  460 MiB/s
Files Completed:     529, Data Written:   2.8GiB, Files Remaining:     477, Cur FPS:    88, Throughput:  479 MiB/s
Files Completed:     672, Data Written:   3.5GiB, Files Remaining:     332, Cur FPS:    96, Throughput:  517 MiB/s
Files Completed:     805, Data Written:   4.3GiB, Files Remaining:     201, Cur FPS:   100, Throughput:  545 MiB/s
Files Completed:     938, Data Written:   4.9GiB, Files Remaining:      67, Cur FPS:   104, Throughput:  562 MiB/s

Done!
Number of Files Written: 1000, Total Size: 5.3GiB, Avg FPS: 100, Avg Throughput: 541 MiB/s, Elapsed Time: 10 seconds
```
