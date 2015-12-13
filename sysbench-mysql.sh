#! /bin/bash

tablesize=10000000

export DEBIAN_FRONTEND=noninteractive
apt-get -q -y --force-yes install mysql-server sysbench

mysql -f -e "drop database sysbench"
mysql -e "create database sysbench"

time sysbench --test=oltp --oltp-table-size=$tablesize \
    --mysql-db=sysbench --mysql-user=root \
    --mysql-password= prepare

for threads in 1 2 4 8 16 32 64 128; do
    for ((iter=1; iter < 4; iter++)); do
        echo "running test with $threads threads, try $iter"
        sysbench --test=oltp --oltp-table-size=$tablesize \
            --mysql-db=sysbench --mysql-user=root \
            --mysql-password= --max-time=60 \
            --oltp-read-only=off --max-requests=0 \
            --num-threads=$threads run 2>&1 > sysbench.$threads.$iter.out
    done
done
