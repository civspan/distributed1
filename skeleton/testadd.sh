echo 'starting script..'
for i in `seq 0 400`
do
    #echo 'POST' 'http://10.1.0.'$((${i}%10+1))':80/board'
    curl -d 'entry='${i} -X 'POST' 'http://10.1.0.'$(((${i} % 8) + 1))':80/board'
done

