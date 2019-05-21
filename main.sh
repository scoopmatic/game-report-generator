cd ../data-processing

python join_annotations.py ../hockey-annotation/events.json ../hockey-annotation/events.txt events_with_annotations.json
python create_training_data.py events_with_annotations.json

cd ../event-selector
sh train_crf.sh

cd ../game-report-generator
python produce_game_input.py > game_inputs.txt
#sh generate_sentences.sh # Point to event-to-sentence generation script
