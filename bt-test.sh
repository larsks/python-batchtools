# BJ
# --------------------------------------------------------------------------------
echo "testing bj valid commands"
python3 batchtools.py bj -h
python3 batchtools.py bj --help

echo "testing bj invalid commands"
python3 batchtools.py bj -z

echo "testing bj command"
br nvidia-smi &
br sleep 10 &
python3 batchtools.py bj


# BD
# ----------------------------------------------------------------------------------

echo "testing bd valid commands"
python3 batchtools.py bd -h
python3 batchtools.py bd --help
br nvidia-smi &
sleep 3
python3 batchtools.py bd

echo "testing bj invalid commands"
python3 batchtools.py bd -z
python3 batchtools.py bd thisisafakejob

#NEED TO ADD CASE FOR SPECIFIED WORKLOAD


# BL
# ----------------------------------------------------------------------------------
echo "testing bl valid commands"
python3 batchtools.py bl -h
python3 batchtools.py bl --help
python3 batchtools.py bl
python3 batchtools.py bl csw-dev-0
br nvidia-smi

# ADD CASES HERE FOR
br sleep 20 &
# Needs bash to get jobs
# python3 batchtools.py bl csw-dev-0 csw-dev-1

echo "testing bl invalid commands"
python3 batchtools.py bl -z
python3 batchtools.py bl thisisafakepod


# BQ
# ----------------------------------------------------------------------------------
echo "testing bq valid commands"
python3 batchtools.py bq -h
python3 batchtools.py bq --help
python3 batchtools.py bq

echo "testing bq invalid commands"
python3 batchtools.py bq randomnewarg
python3 batchtools.py bq -z

# BP
# ------------------------------------------------------------------------------------
echo "testing valid bp commands"
python3 batchtools.py bp -h
python3 batchtools.py bp --help
br nvidia-smi &
python3 batchtools.py bp



# BR
# ----------------------------------------------------------------------------------------
python3 batchtools.py br nvidia-smi
python3 batchtools.py br --wait 0 nvidia-smi
