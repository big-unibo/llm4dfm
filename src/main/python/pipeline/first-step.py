from pathlib import Path
from tqdm import tqdm
from models import Model, load_text_and_first_prompt, is_model_without_chat_constraints
from utils import load_yaml, load_prompts, store_output
import os
import argparse


def log(message):
    print(f'{os.path.splitext(os.path.basename(__file__))[0]} - {message}\n')


parser = argparse.ArgumentParser(description="Process some configuration.")
parser.add_argument('--exercise', help='Exercise to use')
parser.add_argument('--p_version', help='Prompt version to use')
parser.add_argument('--exercise_version', help='Exercise version to use')
args = parser.parse_args()

model_config = load_yaml(f'{Path().absolute()}/pipeline/first-step-config.yml')
key_config = load_yaml(f'{Path().absolute()}/../resources/credentials.yml')

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

    config['key'] = key_config[config['name']]['key']

    model = Model(model_config['use'], config['name'], config, config['key'], model_config['debug_prints'])

else:
    raise Exception("No models")

model_outputs = []
prompts = []

# Check if the --exercise argument is passed
if args.exercise:
    if len(args.exercise.split('/')) > 0:
        exercise = args.exercise.split('/')[-1]
    else:
        exercise = args.exercise
    exercise = '-'.join(Path(exercise).stem.split('-')[:-1])
    ex_name = '-'.join(exercise.split('-')[:2])
    model_config['exercise']['name'] = ex_name
    if args.p_version:
        model_config['exercise']['prompt_version'] = args.p_version
    if args.exercise_version:
        model_config['exercise']['version'] = args.exercise_version
else:
    exercise = '-'.join((model_config['exercise']['name'], model_config['exercise']['version']))

# As new indication, load context prompt and then text exercise and first prompt together
prompts.extend(load_text_and_first_prompt(exercise, model_config['exercise']['prompt_version'], config['name']))
# After, load remaining prompts
prompts.extend(load_prompts(model_config['exercise']['prompt_version'], config['name'])[len(prompts):])

# Used to allow models without chat structure constraints (i.e. after each system or user input require an assistant
# message, so one batch at a time) to batch first system and user input in a single batch
first_batch = 2 if is_model_without_chat_constraints(config['name']) else 1

# batch text and prompts
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

if model_config['debug_prints']:
    log(f'Chat: {model.chat}\nOutput: {model_output}')

chat_input = [sentence for sentence in model.chat if sentence['role'] == 'system' or sentence['role'] == 'user']

# store output
store_output(config, model_config['exercise'], chat_input, model_outputs, model_config['use'] == 'import')
