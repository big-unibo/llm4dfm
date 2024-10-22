import argparse
from pathlib import Path
from tqdm import tqdm
import traceback

from llm4dfm.pipeline.models import Model, load_text_and_first_prompt, is_model_without_chat_constraints
from llm4dfm.pipeline.preprocess import preprocess
from llm4dfm.pipeline.utils import (load_yaml_from_resources, load_prompts, store_output, load_ground_truth_exercise, store_automatic_output,
                   get_timestamp, output_as_valid_yaml, get_dir_label_name, extract_ex_num, label_edges)
from llm4dfm.pipeline.metrics import MetricsCalculator


parser = argparse.ArgumentParser(description="Process some configuration.")
parser.add_argument('--exercise', help='Exercise to use')
parser.add_argument('--p_version', help='Prompt version to use')
parser.add_argument('--exercise_version', help='Exercise version to use')
parser.add_argument('--model', help='Model used')
parser.add_argument('--model_label', help='Model label to use')
parser.add_argument('--dir_label', help='Directory label to use')

args = parser.parse_args()

model_config = load_yaml_from_resources('pipeline-config')
key_config = load_yaml_from_resources('credentials')

# Model loading

if model_config['use'] == 'import':
    raise Exception('import not supported')
    # config = model_config['model_import']
    #
    # config['key'] = key_config[config['name']]['key']
    #
    # model = Model(model_config['use'], config['name'], config, config['key'],
    #               model_config['debug_prints'], config['quantization'])

elif model_config['use'] == 'api':
    config = model_config['model_api']
    if args.model:
        automatic_run = True
        config['name'] = args.model

    config['key'] = key_config[config['name']]['key']
    model = Model(model_config['use'], config['name'], config, config['key'], model_config['debug_prints'])

else:
    raise Exception("No models")

# Argument parsing

automatic_run = False

if args.exercise:
    automatic_run = True
    if len(args.exercise.split('/')) > 0:
        exercise = args.exercise.split('/')[-1]
    else:
        exercise = args.exercise
    exercise = '-'.join(Path(exercise).stem.split('-')[:-1])
    ex_name = '-'.join(exercise.split('-')[:2])
    model_config['exercise']['name'] = ex_name
else:
    exercise = '-'.join((model_config['exercise']['name'], model_config['exercise']['version']))
if args.p_version:
    automatic_run = True
    model_config['exercise']['prompt_version'] = args.p_version
if args.exercise_version:
    automatic_run = True
    model_config['exercise']['version'] = args.exercise_version
if args.model_label:
    automatic_run = True
    config['label'] = args.model_label
if args.dir_label:
    automatic_run = True
    model_config['output']['dir_label'] = args.dir_label

model_config['output']['dir_label'] = get_dir_label_name(model_config['exercise']['version'], model_config['exercise']['prompt_version'], config['label'], model_config['output']['dir_label'])

# Load prompts

model_outputs = []
prompts = []
# As new indication, load context prompt and then text exercise and first prompt together
first_prompt = load_text_and_first_prompt(exercise, model_config['exercise']['prompt_version'], config['name'])
prompts.extend(first_prompt)
# After, load remaining prompts
prompts.extend(load_prompts(model_config['exercise']['prompt_version'], config['name'])[len(first_prompt):])

# Used to allow models without chat structure constraints (i.e. after each system or user input require an assistant
# message, so one batch at a time) to batch first system and user input in a single batch
first_batch = len(first_prompt) if is_model_without_chat_constraints(config['name']) else 1


# Batch text and prompts

with (tqdm(desc=f'Prompt {config["name"]}', total=len(prompts)) as bar_batch):
    if model_config['debug_prints']:
        print(prompts)
    model_output = model.batch(prompts[:first_batch])
    model_outputs.append(model_output)
    bar_batch.update(first_batch)
    for prompt in prompts[first_batch:]:
        model_output = model.batch(prompt)
        model_outputs.append(model_output)
        bar_batch.update(1)

try:
    model_outputs = output_as_valid_yaml(model_outputs)
except:
    store_output(config, model_config['exercise'], model_outputs, model_config['use'] == 'import', {}, get_timestamp(), model_config['output']['dir_label'])
    print("Output not correctly generated")
    exit(1)


if model_config['debug_prints']:
    print(f'Chat: {model.chat}\nOutput: {model_outputs}')

# Load and preprocess ground-truth

ground_truth = load_ground_truth_exercise(model_config['exercise']['name'])

is_demand = model_config['exercise']['version'] == 'demand'

if is_demand:
    ground_truth = ground_truth['demand_driven']
else:
    ground_truth = ground_truth['supply_driven']

# Extracting ex number as last digit in exercise name
ex_num = extract_ex_num(model_config['exercise']['name'])

gt_prep = dict()
gt_prep['dependencies'], gt_prep['measures'], gt_prep['fact'] = preprocess(ex_num, ground_truth['dependencies'],
                                                     ground_truth['measures'] if ground_truth['measures'] else set(),
                                                     ground_truth['fact'], is_demand)

# Calculate metrics

metrics = []

dep_gt = gt_prep['dependencies']
meas_gt = gt_prep['measures']
fact_gt = gt_prep['fact']

metric_calc = MetricsCalculator(fact_gt, meas_gt, dep_gt, ex_num, is_demand)

output_preprocessed = []

for i, output in enumerate(model_outputs):
    try:
        dep_output, meas_output, fact_output = preprocess(ex_num, output['dependencies'],
                                                     output['measures'] if output['measures'] else set(),
                                                     output['fact'], is_demand)
        edges_tp_idx, edges_fp_idx, edges_fn_idx, gt_used = metric_calc.get_edges_idx(fact_output, meas_output,
                                                                                      dep_output)
        tp_nodes, fp_nodes, fn_nodes = metric_calc.get_nodes()

        step_metric = {
            'edges': metric_calc.calculate_metrics_from_preprocessed(edges_tp_idx, edges_fp_idx, edges_fn_idx),
            'nodes': metric_calc.calculate_metrics_nodes(fact_output, meas_output, dep_output)}
        metrics.append(step_metric)

        out, gt = label_edges(output, ground_truth, edges_tp_idx, edges_fp_idx, edges_fn_idx, gt_used)

        output_preprocessed.append({'dependencies': out['dependencies'], 'fact': out['fact'], 'measures': out['measures'],
                               'ground_truth_labels': gt, 'nodes': {'tp': list(tp_nodes), 'fp': list(fp_nodes),
                                                                    'fn': list(fn_nodes)}})
    except:
        traceback.print_exc()
        metrics.insert(i, dict())
        print(f"Output {i}-th not correctly generated, skipped")

# Store results

ts = get_timestamp()

# store output
store_output(config, model_config['exercise'], model_outputs, output_preprocessed, gt_prep, model_config['use'] == 'import', metrics, ts, model_config['output']['dir_label'])

if automatic_run:
    store_automatic_output(config, model_config['exercise'], output_preprocessed, model_config['use'] == 'import', metrics, ts, model_config['output']['dir_label'])