#! /bin/bash


## DOES NOT WORK YET
## Error during test:  FATAL: Cannot open file errno = 22

apt-get -q -y --force-yes install sysbench

for size in 1G 4G 16G; do
   for mode in seqwr seqrd rndrd rndwr rndrw; do
      echo "prep1"
      sysbench --test=fileio --file-num=64 --file-total-size=$size --init-rng=on --file-extra-flags=direct prepare
      echo "prep2"
      # make sure files are not in cache
      for threads in 1 4 8; do
         echo "====== testing $threads threads"
         echo PARAMS $size $mode $threads > sysbench-size-$size-mode-$mode-threads-$threads-fileio.out
         sysbench --test=fileio --file-total-size=$size --file-test-mode=$mode \
            --max-time=60 --max-requests=100000000 --num-threads=$threads --init-rng=on \
            --file-num=64 --file-extra-flags=direct --file-fsync-freq=0 --file-block-size=16384 run \
            | tee -a sysbench-size-$size-mode-$mode-threads-$threads-fileio.out 2>&1
         echo "testing2"
      done
      sysbench --test=fileio --file-total-size=$size cleanup
   done
done
