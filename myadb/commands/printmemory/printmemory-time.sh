#!/bin/sh
dir=/sdcard/log/
if [ ! -d ${dir} ]; then
    mkdir ${dir}
fi
while true
do
    date_str=`date "+%Y%m%d %H:%M:%S"`
    hour=${date_str:9:2}
    if [ $hour -le 12 ]; then
        file="${dir}${date_str:0:8}-1.txt"
    else
        file="${dir}${date_str:0:8}-2.txt"
    fi
    echo "======== ${date_str} begin ========" >> $file
    ps >> $file
    echo "======== ${date_str} end ========" >> $file
    sleep 5
done
