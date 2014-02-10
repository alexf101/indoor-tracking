for i in 10 1000 10000 100000 1000000 2000000 10000000 11000000
do
	bytes=$(yes | head -n $i | tr -d '\n')
	echo doing $i bytes
	(echo delete key; echo set key 0 900 $i; echo $bytes; echo get key; sleep 1) | telnet localhost 11211 > output_$i
	outputsize=$(stat -c%s "output_$i")
	echo output size is $outputsize - should be about $(($i+110))
done
echo delete key | telnet localhost 11211
