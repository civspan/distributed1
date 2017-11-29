for i in `seq 1 10`; do
curl -d 'entry='${i} -X 'POST' 'http://10.1.0.'$i':80/entries'
done

