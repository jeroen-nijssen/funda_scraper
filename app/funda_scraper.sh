#!/bin/sh

working_dir=/app

touch $working_dir/log/funda.log
touch $working_dir/log/pararius.log
touch $working_dir/log/jaap.log

while true
do
echo "Running Lookup for Funda"
python $working_dir/funda.py >> $working_dir/log/funda.log
now=$(date)
echo "Funda Check completed on: $now"
sleep 1h
echo "Running Lookup for Pararius"
python $working_dir/pararius.py >> $working_dir/log/pararius.log
now=$(date)
echo "Pararius Check completed on: $now"
sleep 30m
echo "Running Lookup for Jaap"
python $working_dir/jaap.py >> $working_dir/log/jaap.log
now=$(date)
echo "Jaap Check completed on: $now"
sleep 1h
done
