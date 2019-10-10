#!/bin/sh

#OPTIMAL_MODEL=$(grep -A 2 "improving ppl" training.log | tail -1 | cut -d" " -f6) # Best model by perplexity
OPTIMAL_MODEL="trained_model.pt" # Best model by BLEU, selected by train.sh eval script

## Generate with fixed random seed and beam search
python OpenNMT-py/translate.py -model $OPTIMAL_MODEL -src $1 -output $2 -verbose -n_best 1 -replace_unk -max_length 50

## Generate with random sampling instead of beam search and varying seed
#python ~/arch/OpenNMT-py/translate.py -model $OPTIMAL_MODEL -src $1 -output test_pred.txt -verbose -replace_unk -beam_size 1 -random_sampling_temp 1.0 -random_sampling_topk -1 -seed $(hexdump -d /dev/urandom|head -1|cut -b11-15)
