echo 'starting script..'
for i in `seq 0 300`
do
    #echo 'POST' 'http://10.1.0.'$((${i}%10+1))':80/board'
    curl -d 'entry='${i} -X 'POST' 'http://10.1.0.'$(((${i} % 6) + 1))':80/board'
done

