# Prepare data

cd ../data-processing

python join_annotations.py ../hockey-annotation/events.json ../hockey-annotation/events.txt events_with_annotations.json
python create_training_data.py events_with_annotations.json


# Train event selector CRF and tag validation set (select events)

cd ../event-selector
sh train_crf.sh


# Prepare input for generation

cd ../game-report-generator
python produce_game_input.py > game_inputs.txt


# Train generation model and generate text for events

sh event2text/train.sh
sh event2text/generate.sh

# View results

sh event2text/inspect_preds.sh
