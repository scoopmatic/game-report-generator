""" Prepare input for text generation from event selector predictions and prepared features """

import json

input_data_file = open("../data-processing/selection_val.jsonl")
selection_pred_file = open("../event-selector/crf_val.pred")

seqs = []
last_game = None
for line in input_data_file:
    feats = json.loads(line.strip())
    if last_game != feats['game']:
        try:
            seqs[-1].sort()
        except:
            pass
        seqs.append([])
        last_game = feats['game']
    seqs[-1].append((int(feats['event_idx'][1:]), feats['input']))

all_labels = [[]]
for line in selection_pred_file:
    line = line.strip()
    if line:
        all_labels[-1].append(line == '1')
    else:
        all_labels.append([])

for game_i, labels in enumerate(all_labels):
    for event_i, do_generate in enumerate(labels):
        if do_generate:
            print(seqs[game_i][event_i][1])
    print()
