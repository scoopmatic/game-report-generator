## Prepare data

# Insert annotations into event data
python ../data-processing/join_annotations.py ../hockey-annotation/events.json ../hockey-annotation/events.txt events_Anno.json
# Produce features for events
python create_training_data.py events_Anno.json events_AnnoFeats.json

## Train event selector CRF and tag validation set (select events)

cd ../event-selector
sh train_crf.sh ../game-report-generator/selection_train.jsonl ../game-report-generator/selection_val.jsonl


# Insert selection prediction into events JSON file

cd ../game-report-generator
python insert_selection.py events_AnnoFeats.json selection_val.jsonl ../event-selector/crf_val.pred events_AnnoFeatsSel.json


# Train generation model and generate text for events

#sh event2text/train.sh
#sh event2text/generate.sh

# View results

#sh event2text/inspect_preds.sh
