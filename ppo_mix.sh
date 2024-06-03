# Script to generate the data mix for running PPO.
# Base corpus is:
# https://zenodo.org/records/205950/files/webis-simple-sentences-17-corpus-test.txt.gz?download=1

sentences() {
  MIN_LEN=$1
  MAX_LEN=$2
  CNT=$3
  echo >&2 ${MIN_LEN} ${MAX_LEN} ${CNT}
  zcat data/webis.txt.gz | \
    tr -d '\t' | \
    awk "{if (NF >= ${MIN_LEN} && NF <= ${MAX_LEN}) { print \$0}}" | \
    head -n 1000000 | \
    egrep -v "edit|costs|reservation|hotel|tourist|\?" | \
    egrep -v "^[^A-Za-z]" | \
    sed '/["*()$@]/d' | \
    sed '/^\s*$/d' | \
    sort -u | \
    sort -R | \
    head -n ${CNT} | \
    sort
}


sentences 3 5 20000 > ./data/ppo_mix.txt
sentences 5 10 15000 >> ./data/ppo_mix.txt
sentences 10 15 10000 >> ./data/ppo_mix.txt
sentences 15 20 5000 >> ./data/ppo_mix.txt

sort -R ./data/ppo_mix.txt > data/ppo_mix.shuffled.txt
