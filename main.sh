## Prepare data

# Insert annotations into event data
python ../data-processing/join_annotations.py ../hockey-annotation/train.json ../hockey-annotation/events.txt train_Anno.json
python ../data-processing/join_annotations.py ../hockey-annotation/devel.json ../hockey-annotation/events.txt devel_Anno.json
python ../data-processing/join_annotations.py ../hockey-annotation/test.json ../hockey-annotation/events.txt test_Anno.json

# Produce features for events (required by CRF)
python create_training_data_orig.py train_Anno.json train_input.txt train_output.txt train_selection.jsonl train_AnnoFeats.json
python create_training_data_orig.py devel_Anno.json train_input.txt devel_output.txt devel_selection.jsonl devel_AnnoFeats.json
python create_training_data_orig.py test_Anno.json train_input.txt test_output.txt test_selection.jsonl test_AnnoFeats.json

# Create alternative training data for generation
mkdir event2text/data
python create_training_data.py --json train_Anno.json --mode single > event2text/data/train.all
python create_training_data.py --json devel_Anno.json --mode single > event2text/data/devel.all
python create_training_data.py --json test_Anno.json --mode single > event2text/data/test.all


## Train event selector CRF and tag validation set (select events)

cd ../event-selector
sh train_crf.sh ../game-report-generator/train_selection.jsonl ../game-report-generator/devel_selection.jsonl ../game-report-generator/test_selection.jsonl


# Insert selection prediction into events JSON file

cd ../game-report-generator
python insert_selection.py test_Anno.json test_selection.jsonl ../event-selector/crf_val.pred test_AnnoSel.json


# Train generation model and generate text for events

cd event2text
bash train.sh
#sh generate.sh

# View results

#sh inspect_preds.sh
