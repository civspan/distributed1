for i in `seq 1 20`; do
curl -d 'entry=t'${i} -X 'POST' 'http://10.1.0.${i}:80/entries'
done
