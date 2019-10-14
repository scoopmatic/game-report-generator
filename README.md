# Game report generator

The <code>main.sh</code> script calls upon scripts to:
* Join game statistics data with annotations and prepare features
* Train event selector model and select events from games in test set
* Train and evaluate generation model
* Generate text from game events (disabled by default)

For instructions how to invoke the event selection model for any input see the [API repository](https://github.com/scoopmatic/gen_api/blob/master/selector_pipeline.sh).

For more general information, see the [paper repository](https://github.com/scoopmatic/finnish-hockey-news-generation-paper).


