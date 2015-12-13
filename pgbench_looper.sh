#!/bin/bash

host="$(hostname)"
timeslot=`date +%Y%m%d_%H-%M`
logfile="/tmp/$host-$timeslot-pgbench.log"
csvfile="/tmp/$host-$timeslot-pgbench.csv"
customfile="/tmp/$host-$timeslot-pgbench.sql"
customsql="SELECT sum(generate_series) FROM generate_series(1,100000);"
customdb="TEST"
kernel="$(uname -a)"
kernel_params="$(sysctl -p)"
rc_local="$(cat /etc/rc.local)"
ram="$(cat /proc/meminfo | grep MemTotal)"
cores="$(nproc)"
cpudata="$(lscpu)"
disk_controllers="$(lspci | grep -E 'RAID|SCSI|IDE|SATA')"
mounts="$(cat /etc/mtab)"
pguser="pgcontrol"
scale=500
runs=2000
max_clients=256
clients_inc=8
repeat=3

echo "Host,Test,Scale,Runs,Clients,Iteration,TPS (exc),TPS (inc)" > $csvfile
printf %100s |tr " " "=" > $logfile
echo "### Starting pgbench testing on $host at $timeslot" >> $logfile
echo "### Running kernel: $kernel" >> $logfile
echo "### Running kernel parameters: $kernel_params" >> $logfile
echo "### Local parameters: $rc_local" >> $logfile
echo "### Total CPU Cores: $cores" >> $logfile
echo "### CPU data: $cpudata" >> $logfile
echo "### $ram" >> $logfile
echo "### Disk controllers: $disk_controllers" >> $logfile
echo "### Mounts: $mounts" >> $logfile

printf %100s |tr " " "-" >> $logfile
echo "### Creating pgbench database" >> $logfile
result=`psql -U $pguser -d postgres -c 'DROP DATABASE IF EXISTS "pgbench";'`
echo $result >> $logfile
result=`createdb pgbench -U $pguser 2>&1`
echo $result >> $logfile

echo "### Creating populating database with scaling factor of $scale" >> $logfile
result=`pgbench -i -s $scale pgbench -U $pguser 2>&1`
echo $result >> $logfile

printf %100s |tr " " "-" >> $logfile
echo "### Running read only tests" >> $logfile
for i in $(eval echo {8..$max_clients..$clients_inc}); do
	echo "##Running test with $i clients" >> $logfile
	for j in $(eval echo {1..$repeat}); do 
		result=`pgbench -t $runs -c $i -S pgbench -U $pguser 2>&1`
		echo "#Run $j: $result" >> $logfile
		csvdata=$(echo "$result" | grep tps | cut -d "=" -f2 | cut -d "(" -f1 | sed -e 's/^[ \t]*//' | tr '\n' ',')
		echo "$host,Read Only,$scale,$runs,$i,$j,$csvdata" >> $csvfile
	done
done

printf %100s |tr " " "-" >> $logfile
echo "### Running read write tests" >> $logfile
for i in $(eval echo {8..$max_clients..$clients_inc}); do
	echo "##Running test with $i clients" >> $logfile
	for j in $(eval echo {1..$repeat}); do 
		result=`pgbench -t $runs -c $i pgbench -U $pguser 2>&1`
		echo "#Run $j: $result" >> $logfile
		csvdata=$(echo "$result" | grep tps | cut -d "=" -f2 | cut -d "(" -f1 | sed -e 's/^[ \t]*//' | tr '\n' ',')
		echo "$host,Read Write,$scale,$runs,$i,$j,$csvdata" >> $csvfile
	done
done

printf %100s |tr " " "-" >> $logfile
echo "$customsql" > $customfile
echo "### Running custom tests" >> $logfile
for i in $(eval echo {8..$max_clients..$clients_inc}); do
        echo "##Running test with $i clients" >> $logfile
        for j in $(eval echo {1..$repeat}); do
                result=`pgbench -n -f $customfile -t $runs -c $i $customdb -U $pguser 2>&1`
                echo "#Run $j: $result" >> $logfile
		csvdata=$(echo "$result" | grep tps | cut -d "=" -f2 | cut -d "(" -f1 | sed -e 's/^[ \t]*//' | tr '\n' ',')
		echo "$host,Custom,$scale,$runs,$i,$j,$csvdata" >> $csvfile
        done
done

rm $customfile
echo "### Done" >> $logfile
printf %100s |tr " " "=" >> $logfile