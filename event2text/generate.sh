#!/bin/sh

export $(cat config.sh)

OPTIMAL_MODEL=$(grep -A 2 "improving ppl" training.log | tail -1 | cut -d" " -f6)

cat ../game_inputs.txt | egrep -v "^$" > data/game_inputs.txt_

## Generate with fixed random seed and beam search
python $ONMT_PATH/translate.py -model $OPTIMAL_MODEL -src data/game_inputs.txt_ -output test_pred.txt -verbose -n_best 1

## Generate with random sampling instead of beam search and varying seed
#python ~/arch/OpenNMT-py/translate.py -model $1 -src ../game_nputs.txt -output test_pred.txt -verbose -replace_unk -beam_size 1 -random_sampling_temp 1.0 -random_sampling_topk -1 -seed $(hexdump -d /dev/urandom|head -1|cut -b11-15)

