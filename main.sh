## Prepare data

# Insert annotations into event data
python ../data-processing/join_annotations.py ../hockey-annotation/events.json ../hockey-annotation/events.txt events_Anno.json
# Produce features for events (required by CRF)
python create_training_data_orig.py events_Anno.json events_AnnoFeats.json
## call python create_trainin_data.py to create alternative training data for generation

## Train event selector CRF and tag validation set (select events)

cd ../event-selector
sh train_crf.sh ../game-report-generator/selection_train.jsonl ../game-report-generator/selection_val.jsonl


# Insert selection prediction into events JSON file

cd ../game-report-generator
python insert_selection.py events_AnnoFeats.json selection_val.jsonl ../event-selector/crf_val.pred events_AnnoFeatsSel.json


# Train generation model and generate text for events

cd event2text
#sh train.sh
#sh generate.sh

# View results

#sh inspect_preds.sh
