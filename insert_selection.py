""" Insert predicted event selection into event JSON """

import json
import sys


all_event_data = json.load(open("../data-processing/events_with_annotations.json_"))
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
    seqs[-1].append((int(feats['event_idx'][1:]), feats))

all_labels = [[]]
for line in selection_pred_file:
    line = line.strip()
    if line:
        all_labels[-1].append(line == '1')
    else:
        all_labels.append([]) # New article

for game_i, labels in enumerate(all_labels):
    for event_i, do_generate in enumerate(labels):
        game = seqs[game_i][event_i][1]['game']
        event = seqs[game_i][event_i][1]['event_idx']
        for ev in all_event_data[game]['events']:
            if ev['event_idx'] == event:
                ev['selected'] = do_generate*1


json.dump(all_event_data, open("events_master.json", 'w'), indent=2, sort_keys=False)
