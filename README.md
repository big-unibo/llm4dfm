# Conceptual Design of Multidimensional Cubes with LLMs: An Investigation

[![build](https://github.com/big-unibo/experimental-project/actions/workflows/build.yml/badge.svg)](https://github.com/big-unibo/experimental-project/actions/workflows/build.yml)

A research project by the [Business Intelligence Group](http://big.csr.unibo.it).

Index of this repository.
- [Project structure](#project-structure): gives an overview of the repository.
- [Research data](#research-data): shows the input used and output obtained in our research activity.
- [Usage](#usage): explains how to use the code to run new experiments.

IMPORTANT: to run the project, an active account on OpenAI is needed to connect to ChatGPT via API.

## Project structure

    datasets/                   -- where case studies are stored
        *-text.yml                -- input of the case study
        *-ground-truth.yml        -- expected result
    inputs/                     -- where prompt templates are stored
    outputs/                    -- where generated outputs are stored (not committed)
    results/                    -- where final results are stored (committed)
    llm4dfm/                    -- source code
    tests/                      -- test code

The module `llm4dfm/pipeline` contains Python files implementing a pipeline enabling the systematic interaction with an LLM.

- `models.py`   -- contains model's utils
- `pipeline.py` -- contains the whole process of importing, batching, querying and storing metrics
- `metrics.py` -- contains the process of calculating metrics (precision, recall, f1-measure)
- `preprocess.py` -- contains the preprocessing phase (e.g., to remove spaces and underscores)
- `utils.py`    -- contains general utils
- `csv_graph.py`    -- contains the process to generate graphs
- `graph_utils.py`    -- contains utils used to work with graph, such as metrics calculation
- `.env`        -- contains information about program's paths - must be created when cloning the repo, based on `.env-example`

Configuration files and scripts to automate multiple executions of the pipeline are collected in the `llm4dfm/resources` module. If not present when cloning the repo, the file must be created based on the respective `(filename)-example.yml` version.

- `credentials.yml`  -- contains configuration needed to connect to cloud APIs
- `preprocess.yml` -- contains preprocessing rules to apply (thesaurus)
- `pipeline-config.yml`  -- contains configuration of a single run
- `metrics-config.yml` -- contains configuration of metrics
- `csv-graph-config.yml`  -- contains configuration of graphs generated from the resulting csv file
- `automatic-run.sh`  -- script to automate the execution of multiple pipeline
- `automatic-metrics.sh`  -- script to automate the recalculation of metrics on obtained outputs
- `yml.html`  -- script to compare ground-truth and output via visualisation

## Research data

The data you want to look at is summarized here.

- Prompt templates for the research questions are in the `input` folder.
- Case studies are in the `datasets` folder, called "exercises"; for each of them, you can find:
  - The supply-driven requirements with tables described with logical schema: `original-text`
  - The supply-driven requirements with tables described with SQL DDL: `sql-text`
  - The demand-driven requirements: `demand-text`
  - The ground truth for both supply- and demand-driven requirements: `ground-truth`
- The thesaurus used for equivalence rules in demand-driven design is in the `llm4dfm/resources/preprocess.yml` file
- The results of all interactions  with ChatGPT are in the `results` folder; for each research question, you can find:
  - The 10 interactions for every case study
  - A CSV file summarizing all obtained outputs and the calculated metrics
  - Charts showing, for each case study:
    - The average F1-measure
    - Average precision and recall on nodes 
    - Average precision and recall on edges
    - Boxplot of F1-measures on nodes 
    - Boxplot of F1-measures on edges 
- An example of a full interaction with ChatGPT (taken from one of the interactions for RQ5 on case study 7) is shown in `results/full-chat-example-rq5-exercise7.json`

### Analyzing results

To analyze the output obtained from ChatGPT, the static web application at `llm4dfm/resources/yml.html` can be used.
  - Open the page on your browser
  - Load one of the output .yml files
  - Use the available buttons to either draw the ground truth's DFM, draw the LLM's DFM, or draw a comparison of the two DFMs.
    - True positives (on both nodes and edges) are indicated in green
    - False positives (on both nodes and edges) are indicated in red
    - False negatives (on both nodes and edges) are indicated in grey
    - Nodes are indicated in yellow if they are present in the LLM's output with contradicting roles (e.g., both as dimensional attribute and measure), one of them being correct and the other wrong
    - Comparison metrics (precision, recall, and F1-measure) are indicated to the right

## Usage

### Installation

The project has been developed with Python 3.12. 

#### Venv

It is recommended to manage Python dependencies through virtual environments. See [here](https://docs.python.org/3/library/venv.html).

> The .venv module provides support for creating lightweight "virtual environments" with their own site directories, optionally isolated from system site directories. Each virtual environment has its own Python binary (which matches the version of the binary that was used to create this environment) and can have its own independent set of installed Python packages in its site directories.

In case .venv folder is not created, venv can be created through

```bash
python -m venv .venv
```

To activate venv in Windows (with bash shell; e.g., git bash)
```bash
source .venv/Scripts/activate
```

To activate venv in Linux
```bash
source .venv/bin/activate
```

#### Requirements

Poetry is used to manage automatic testing; you can skip its installation if you are interested only in the execution of the pipeline.

- Install dependencies without Poetry
  ```bash
  pip install -r requirements.txt
  ```
- Install dependencies with Poetry
  ```bash
  curl -sSL https://install.python-poetry.org | python3 -
  poetry install
  ```


### Configuration 

#### Required configuration parameters

Inside the `pipeline` module, a `.env` file must be provided with the following configurations:
- `DATASETS`   -- path to folder containing exercise (case study) texts
- `OUTPUTS`    -- path to folder in which outpust are stored
- `AUTO_OUTPUTS`    -- path to folder in which outpust of automatic runs are stored
- `RESULTS`   -- path to folder in which results are stored
- `INPUTS`   -- path to folder containing exercise prompts
- `SAVE_MODELS`   -- path to folder in which store imported models

If using Azure to interact with model's API, these configurations must be provided too (model_name must be uppercase)
- `ENDPOINT_{model-name}`

#### Authentication key

The authentication key to connect to the API endpoint must be stored in `llm4dfm/resources/credentials.yml`;
an example of how the config is structured can be found in `llm4dfm/resources/credentials-example.yml`.

#### Pipeline parameters

The following parameters can be configured in `llm4dfm/resources/pipeline-config.yml` file.

Model

- `name`        -- model's name (can be a generalization, such as llama-2, the exact name is stored in "models.py" file, if not present you must add it there)`
- `label`     -- model's name used in output file name generated, if not specified it uses name`
- `deployment`     -- Deployment name for azure distribution [test-gpt-35, test-gpt-4o]`
- `api_version`     -- api model's version`
- `max_tokens` -- it's the maximum length of the generated output`
- `n_response` -- regulates number of responses the model generates`
- `temperature` -- threshold between 0 and 2 that specifies willing to generate more random answers as growing to 2 [0, ..., 1] [Default 0.1]`
- `stop`        -- set the stop character(s, if list) that terminate the response when encountered`
- `top_p` -- threshold between 0 and 1 that specifies willing to use a wider set of words as growing to 1 [0, ..., 1]`
- `top_k` -- threshold between 1 and 40 that specifies the number of tokens (with the highest probability) considered for the next generation. Less randomness for lower values [could be only a gemini parameter]`

Exercise

- `name`           -- the exercise name (part before version, exercise-N)`
- `version`           -- the exercise version (part between exercise-N- and text.yml) [sql, original, demand]`
- `prompt_version` -- the prompt version (part between prompts- and .yml)`
- `number` -- the exercise number`

General

- `debug_prints`   -- enable output prints during execution`

Output

- `dir_label` -- the label used in output directory name`

#### CSV-Graph

The following parameters can be configured in `llm4dfm/resources/csv-graph-config.yml` file.

- `dir` -- full directory name, in case it's specified all other parameters will be ignored`
- `v` -- the exercise version (part between exercise-N- and text.yml) [sql, original, demand]`
- `prompt_v` -- the prompt version (part between prompts-v and .yml)`
- `model_label` -- model's label name`
- `dir_label` -- directory in which store file name`

#### Metrics

The following parameters can be configured in `llm4dfm/resources/metrics-config.yml` file, under the `exercise` section.

- `dir` -- the exercise's directory inside outputs folder`
- `name` -- the exercise name without .yml extension`
- `demand` -- whether it's a demand driven exercise [true, false]`
- `gt` -- the ground truth's exercise`
- `number` -- the exercise number`

#### Preprocessing

In order to apply equality or ignore rules, `llm4dfm/resources/preprocess.yml` file has been provided.
It is split in 2 sections, the first one is the common, that is applied to all exercises, and then rules for each exercise.

Structure of each section is as follows:
```
1:
  demand:
    equals:
    - item_to_keep_1:
      - elem_1_equal_item_to_keep_1
      - elem_2_equal_item_to_keep_1
    - item_to_keep_2:
      - elem_1_equal_item_to_keep_2
      - elem_2_equal_item_to_keep_2
    ignore:
    - elem_to_ignore_1
    - elem_to_ignore_2
  supply:
    equals:
    - item_to_keep_1:
      - elem_1_equal_item_to_keep_1
      - elem_2_equal_item_to_keep_1
    ignore: []
```

This state that in exercise 1 all elem_1_equal_item_to_keep_1 and elem_2_equal_item_to_keep_1 found in demand exercise
will be preprocessed in item_to_keep_1 and so on, and all dependencies that will have elem_to_ignore_1 or elem_to_ignore_2
will be ignored after preprocessing.
Thesaurus rules are applied here.

### Single run

- Setup [authentication](#authentication-key)
- Configure [pipeline](#Pipeline), and [graph](#CSV-Graph)
- Run `python pipeline/pipeline.py` from `llm4dfm` directory.
  If no Exceptions raised, in `outputs` directory a new directory with a file `/{exercise-version}-{exercise-prompt_version}-{model-label}-{dir_label}/{exercise.name}-{exercise.version}-{exercise.prompt_version}-{model.label}-{new_timestamp}.yml` is generated. Its structure is as follows:
  - config:
    - name: gpt
    - version: 3.5-turbo
    - max_tokens: null 
    - n_responses: 1
    - stop: null
    - top_p: 0.9
    - top_k: 5
  - output:
    - fact:
        name: FACT_NAME
      measures: 
      - name: MEASURE1_NAME
      - name: MEASURE2_NAME
      dependencies:
      - from: TABLE1.Attr
      - to: TABLE2.Attr
      - ...
    - fact:
      name: FACT_NAME
      measures:
      - name: MEASURE1_NAME
      - name: MEASURE2_NAME
      dependencies:
      - from: TABLE1.Attr
      - to: TABLE2.Attr
      - ...
  - output_preprocessed:
    - fact:
      name: FACT_NAME
      measures:
      - name: MEASURE1_NAME
      - name: MEASURE2_NAME
      dependencies:
      - from: TABLE1.Attr
        label: tp
        to: TABLE2.Attr
      - ...
      ground_truth_labels:
        dependencies:
        - from: TABLE1.Attr
          label: tp
          to: TABLE2.Attr
        - ...
        fact:
          name: FACT_NAME
        measures:
        - name: MEASURE1_NAME
        - name: MEASURE2_NAME
    - fact:
      name: FACT_NAME
      measures:
      - name: MEASURE1_NAME
      - name: MEASURE2_NAME
      dependencies:
      - from: TABLE1.Attr
        label: tp
        to: TABLE2.Attr
      - ...
      ground_truth_labels:
        dependencies:
        - from: TABLE1.Attr
          label: tp
          to: TABLE2.Attr
        - ...
        fact:
          name: FACT_NAME
        measures:
        - name: MEASURE1_NAME
        - name: MEASURE2_NAME
  - gt_preprocessed:
    - fact:
      name: FACT_NAME
      measures:
      - name: MEASURE1_NAME
      - name: MEASURE2_NAME
      dependencies:
      - from: TABLE1.Attr
      - to: TABLE2.Attr
      - ...
    - fact:
      name: FACT_NAME
      measures:
      - name: MEASURE1_NAME
      - name: MEASURE2_NAME
      dependencies:
      - from: TABLE1.Attr
      - to: TABLE2.Attr
      - ...
  - metrics:
    - edges:
        precision: [0.0 - 1]
        recall: [0.0 - 1]
        f1: [0.0 - 1]
      nodes:
        precision: [0.0 - 1]
        recall: [0.0 - 1]
        f1: [0.0 - 1]
    - edges:
        precision: [0.0 - 1]
        recall: [0.0 - 1]
        f1: [0.0 - 1]
      nodes:
        precision: [0.0 - 1]
        recall: [0.0 - 1]
        f1: [0.0 - 1]

- Configure [graph](#CSV-Graph)
- Run `python pipeline/csv_graph.py` from `llm4dfm` directory.
  If no Exceptions raised, in `outputs/{csv_graph-v}-{csv_graph-prompt_v}-{csv_graph-model_label}-{csv_graph-dir_label}/` directory, new graph files named `graph-boxplot_f1_edges.pdf, graph-boxplot_f1_nodes.pdf, graph-f1_scores_edges_nodes.pdf, graph-precision_recall_edges.pdf, graph-precision_recall_nodes.pdf` are generated aggregating precision, recall and f1-measure collected in the csv file inside `outputs/{csv_graph-v}-{csv_graph-prompt_v}-{csv_graph-model_label}-{csv_graph-dir_label}/` directory.
Example of run:
`python pipeline/csv_graph.py --exercise_v sql --prompt_version v4 --model gpt4o --runs 1 --label test`

- Configure [metrics](#Metrics)
- Run `python pipeline/metrics.py` from `llm4dfm` directory.
  If no Exceptions raised, in selected exercise file, metrics section is added/overridden. In case preprocessed ground truth and output are not present, standard ones are used.

### Automatic run

First of all, execution privileges must be granted by means of `chmod 700 ./resources/automatic-run.sh`.

After activating [venv](#Venv), a task triggered by
`poetry poe automatic_run` run the pipeline with the following configurations:
- `number_of_runs` -- set number of runs, 1 by default
- `file_version` -- set file version [sql, original, demand], sql by default
- `prompt_version` -- set prompt version [v1, v2, v3, v4, demand], v4 by default
- `model` -- model to use in run
- `"<ex1> ... <fileN>"` -- set exercises to run, all files matching previous configurations by default
- `model_label` -- an optional model label used in yml output generated, empty string by default, if empty model name is used
- `dir_label` -- an optional label used in output directory generated, if not provided a timestamp is generated

This could also be achieved by directly run `./resources/automatic-run.sh` from `llm4dfm` directory, with configurations as stated before.

All configurations specified as argument **override** the ones provided by configuration file ones.
If not specified, optional parameters are read by configuration files instead, all **except** dir_label, that in place of automatic run is generated if not given.

Example of run:
`poetry poe automatic_run 1 sql rq3-alg-base gpt "1 2 3 4 5 6 7 8 9" gpt4o test-after-poetry`
`./resources/automatic-run.sh 1 sql rq3-alg-base gpt "1 2 3 4 5 6 7 8 9" gpt4o example`

Output:
Generate one output file for each run on each file as described before inside `outputs/{file_version}-{prompt_version}-{model_label}-{dir_label}/`.
Additionally, a csv file `output-{file_version}-{prompt_version}-{model_label}-{dir_label}.csv` is generated if not present, else is enriched with run output.
Moreover, `pipeline/csv_graph.py` is run too, generating graphs.

### Automatic metrics

First of all, execution privileges must be granted by means of `chmod 700 ./resources/automatic_metrics.sh`.

**It is noticeable to say that exercise number has to be extracted from exercises' names. Depending on exercises name convention in directory where to iterate, it's provided inside script a default function collecting first numeric occurrence, but also a commented one enabling last occurrence in file names**

After activating [venv](#Venv) from `llm4dfm` root directory via `source .venv/bin/activate`, a task triggered by
`poetry poe automatic_metrics` run the program with the following configurations:

- `dir` -- the directory name inside 'outputs' folder
- `version` -- the prompt version used [sql, demand], sql by default

This could also be achieved by directly run `./resources/automatic-metrics.sh` from `llm4dfm` directory, with configurations as stated before.

Example of run:
`poetry poe automatic_metrics demand-rq5-example-gpt4o-demand demand`
`./resources/automatic-metrics.sh 1 demand-rq5-example-gpt4o-demand demand`

Output:
File preprocess and metrics calculation will be executed, results will be overridden in same file.

### Tests

To execute the tests' suite, inside `llm4dfm` root directory, run 
```bash
poetry poe test
```
