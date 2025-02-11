import os
from copy import deepcopy
import pandas as pd

from dotenv import load_dotenv
import yaml
from datetime import datetime
import re
import csv

load_dotenv()

base_path = os.path.dirname(os.path.abspath(__file__))

datasets = f'{base_path}/{os.getenv('DATASETS')}'
outputs = f'{base_path}/{os.getenv('OUTPUTS')}'
results = f'{base_path}/{os.getenv('RESULTS')}'
inputs = f'{base_path}/{os.getenv('INPUTS')}'
auto_outputs = f'{base_path}/{os.getenv('AUTO_OUTPUTS')}'
resources = f'{base_path}/../resources/'

# General utils

def get_timestamp():
    return datetime.now().strftime('%Y-%m-%dT%H-%M-%S')

# Standard names utils

def get_dir_label_name(ex_version, prompt_version, model_label, dir_label):
    return f"{ex_version}-{prompt_version}-{model_label}-{dir_label}"

# Extract exercise number based on last digit of exercise name
def extract_ex_num(ex_name):
    numbers = re.findall(r'\d+', ex_name)  # Find all sequences of digits
    if numbers:
        return int(numbers[-1])
    else:
        # print("No exercise numbers in exercise name.")
        return None

# Yaml utils

# return yaml configurations as dict
def load_yaml(yaml_file) -> dict:
    with open(f'{yaml_file}.yml', 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

# return yaml configurations as dict
def load_yaml_from_resources(yaml_filename) -> dict:
    return load_yaml(f'{resources}{yaml_filename}')

def write_yaml(yaml_file, data):
    with open(f'{yaml_file}.yml', 'w+', encoding='utf-8') as file:
        yaml.dump(data, file)

def load_full_path_csv(path):
    with open(f'{path}', 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        return [row for row in reader]

# return the text of exercise given ex_name
def load_text_exercise(ex_name):
    return load_yaml(f'{datasets}{ex_name}-text')['text']

# return the ground truth of exercise given ex_name
def load_ground_truth_exercise(ex_name, full_name=''):
    if full_name:
        file_name = '-'.join(full_name.split('-')[:2])
    else:
        file_name = ex_name
    return load_yaml(f'{datasets}{file_name}-ground-truth')

# return prompts of exercise as a dict given ex_name and model_name
def load_prompts(version, model_name):
    return load_yaml(f'{inputs}prompts-{version}')[model_name]

# load output exercise used in second-step and its filename (used after to store the image)
def load_output_exercise(dir_name, full_name):
    return load_yaml(f'{outputs}{dir_name}/{full_name}')

def label_edges(out, gt, tp_idx, fp_idx, fn_idx, gt_used):
    out_to_return = deepcopy(out)
    gt_to_return = deepcopy(gt)
    for idx, dep in enumerate(out_to_return['dependencies']):
        if idx in tp_idx:
            dep['label'] = 'tp'
        elif idx in fp_idx:
            dep['label'] = 'fp'
        else:
            dep['label'] = 'error'
    for idx, dep in enumerate(gt_to_return['dependencies']):
        if idx in gt_used:
            dep['label'] = 'tp'
        elif idx in fn_idx:
            dep['label'] = 'fn'
        else:
            dep['label'] = 'error'
    return out_to_return, gt_to_return


# Map output to a valid yaml as dict
def output_as_valid_yaml(model_outputs):
    return [yaml.safe_load(out.replace('`', '').replace('yaml', '')
                           .replace('`', '').replace('\\n', '\r\n')) if isinstance(out, str)
                            else out for out in model_outputs]


# Store output utils

# add properties to dict_to_store as property:dict_property[property] if present
def add_property_if_present(dict_to_store, props, dict_property):
    for prop in props:
        if prop in dict_property:
            dict_to_store[prop] = dict_property[prop]


def config_to_print(configs) -> dict:
    conf_to_print = {}
    add_property_if_present(conf_to_print, [
        'name',
        'label',
        'deployment',
        'api_version',
        'temperature',
        'max_tokens',
        'n_responses',
        'stop',
        'top_p',
        'top_k',
    ], configs)
    return conf_to_print

# write model_output in file ex_name-model-timestamp.yml
# model_output is the list of outputs
def store_output(model_config, ex_config, model_output, output_preprocessed, gt_preprocessed, metrics, timestamp, dir_label):
    results_output = {
        'config': config_to_print(model_config),
        'output': model_output,
        'output_preprocessed': output_preprocessed,
        'gt_preprocessed': gt_preprocessed,
        'metrics': metrics,
    }

    prompt_version = ex_config['prompt_version']
    ex_name = '-'.join((ex_config['name'], ex_config['version']))
    model = model_config['label'] if model_config['label'] != '' else model_config['name']

    os.makedirs(f'{outputs}{dir_label}', exist_ok=True)

    error = ""
    if metrics=={}:
        error = "-error"

    write_yaml(f'{outputs}{dir_label}/{ex_name}-{prompt_version}-{model}-{timestamp}{error}', results_output)


# write model_output in file ex_name-model-timestamp.yml
# model_output is the list of outputs
def store_additional_properties(dir_label, ex_name, props):
    prev_out = load_yaml(f'{outputs}{dir_label}/{ex_name}')

    for prop in props:
        prev_out[prop] = props[prop]
    write_yaml(f'{outputs}{dir_label}/{ex_name}', prev_out)



def get_csv_file_from_output_dir(dir_name):
    directory = f'{outputs}{dir_name}'
    file = f'output-{dir_name}.csv'

    return os.path.join(directory, file)


def get_headers_csv():
    return ['ex_name','ex_version','ex_prompt_version','ex_number','timestamp','index','config_name','config_label',
            'config_deployment','config_api_version','config_temperature','config_max_tokens','config_n_responses',
            'config_stop','config_top_p','config_top_k','fact','measures','dependencies','node_tp','node_fp','node_fn',
            'edges_tp','edges_fn','edges_fp','edges_precision','edges_recall','edges_f1','nodes_tp','nodes_fn',
            'nodes_fp','nodes_precision','nodes_recall','nodes_f1']


def store_automatic_output(model_config, ex_config, output_preprocessed, metrics_list, timestamp, label_dir):
    for i, metrics in enumerate(metrics_list):
        data = dict()

        for key, value in ex_config.items():
            data[f"ex_{key}"] = value

        data["timestamp"] = timestamp

        data['index'] = i+1

        for key, value in config_to_print(model_config).items():
            data[f"config_{key}"] = value

        data['fact'] = output_preprocessed[i]['fact']['name']

        data['measures'] = [measure['name'] for measure in output_preprocessed[i]['measures']] if output_preprocessed[i]['measures'] else None

        data['dependencies'] = [dependency for dependency in output_preprocessed[i]['dependencies']]

        for node in output_preprocessed[i]['nodes']:
            data[f'node_{node}'] = output_preprocessed[i]['nodes'][node]

        for elem in metrics:
            for met, val in metrics[elem].items():
                data[f"{elem}_{met}"] = val

        file_path = get_csv_file_from_output_dir(label_dir)

        write_headers = False
        headers = get_headers_csv()

        for head in headers:
            if head not in data:
                data[head] = None

        try:
            # Attempt to read the first row (headers) from the CSV file
            with open(f'{file_path}', 'r+') as file:
                reader = csv.reader(file)
                existing_headers = next(reader)  # Read the first row (headers)

            # Check if the existing headers match the desired headers
            # TODO what to do in this case?
            if existing_headers != headers:
                print(f"Headers do not match\nActual:{existing_headers}\nNew: {headers}\nAttempt to write data anyway.")
        except:
            write_headers = True

        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(f'{file_path}', "a+", newline="") as csv_file:
            writer = csv.writer(csv_file)
            if write_headers:
                writer.writerow(headers)
            writer.writerow(list(data.values()))


def update_csv(dir_name, timestamp, ex_name, ex_num, ex_version, output_preprocessed, metrics_list):
    path = get_csv_file_from_output_dir(dir_name)

    os.makedirs(os.path.dirname(path), exist_ok=True)

    try:
        df = pd.read_csv(path)
    except:
        df = pd.DataFrame(columns=get_headers_csv())

    for idx, metrics in enumerate(metrics_list):
        if not df.empty:
            missing_headers = [col for col in get_headers_csv() if col not in df.columns]

            # Add missing headers with default NaN values
            for col in missing_headers:
                df[col] = pd.NA
            matching_rows = (df['ex_number'] == ex_num) & (df['timestamp'] == timestamp) & (df['index'] == idx+1)
        else:
            matching_rows = None

        data = dict()

        data['fact'] = output_preprocessed[idx]['fact']['name']

        data['measures'] = [measure['name'] for measure in output_preprocessed[idx]['measures']] if output_preprocessed[idx]['measures'] else None

        data['dependencies'] = [dependency for dependency in output_preprocessed[idx]['dependencies']]

        for node in output_preprocessed[idx]['nodes']:
            data[f'node_{node}'] = output_preprocessed[idx]['nodes'][node]

        for elem in metrics:
            for met, val in metrics[elem].items():
                data[f"{elem}_{met}"] = val
        if not df.empty and (not matching_rows is None) and matching_rows.any():
            for prop in data:
                df.loc[matching_rows, prop] = str(data[prop])
        else:
            data['ex_name'] = ex_name
            data['ex_version'] = ex_version
            data['ex_number'] = ex_num
            data['timestamp'] = timestamp
            data['index'] = idx + 1

            df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    df.to_csv(path, index=False)

