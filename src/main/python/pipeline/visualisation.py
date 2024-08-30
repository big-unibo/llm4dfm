from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import matplotlib.lines as mlines
import argparse

from graph_utils import load_edges, load_nodes
from visualisation_utils import (preprocess_dependencies_attributes, store_image, short_names_from_tables,
                                 get_tp_fn_fp_edges_to_list)
from utils import load_yaml, load_ground_truth_exercise, load_output_exercise_and_name

parser = argparse.ArgumentParser(description="Process some configuration.")
parser.add_argument('--exercise', help='Exercise to use')
parser.add_argument('--p_version', help='Prompt version to use')
parser.add_argument('--exercise_version', help='Exercise version to use')
args = parser.parse_args()

# Load config
input_config = load_yaml(f'{Path().absolute()}/../resources/visualisation-config.yml')

# Check if the --exercise argument is passed
if args.exercise:
    if len(args.exercise.split('/')) > 0:
        exercise = args.exercise.split('/')[-1]
    else:
        exercise = args.exercise
    exercise = '-'.join(Path(exercise).stem.split('-')[:-1])
    ex_name = '-'.join(exercise.split('-')[:2])

    input_config['exercise']['full_name'] = ''
    input_config['exercise']['latest'] = True
    input_config['exercise']['name'] = ex_name
    input_config['visualisation']['show_graph'] = False
    if args.p_version:
        input_config['exercise']['prompt_v'] = args.p_version
    if args.exercise_version:
        input_config['exercise']['v'] = args.exercise_version

ex_config = input_config['exercise']
model_config = input_config['model']

# Load exercise
ex_output, ex_name = load_output_exercise_and_name(ex_config['name'], ex_config['v'], ex_config['prompt_v'],
                                 model_config['name'], model_config['v'],
                                 ex_config['latest'], ex_config['timestamp'], ex_config['full_name'])
ground_truth = load_ground_truth_exercise(ex_config['name'], ex_config['full_name'])

metrics = ex_config['metrics']

if ex_config['v'] == 'demand':
    ground_truth = ground_truth['demand_driven']
else:
    ground_truth = ground_truth['supply_driven']

# Extract dependencies
try:
    dep_output = ex_output['output']['dependencies'] if ex_output['output'] is dict else ex_output['output'][0]['dependencies']
except:
    print("Dependencies were not correctly generated")
    exit(1)

dep_gt = ground_truth['dependencies']

dep_output_to_use = [{k.lower(): v.lower() for k, v in d.items()} for d in dep_output]
dep_gt_to_use = [{k.lower(): v.lower() for k, v in d.items()} for d in dep_gt]

# Load edges
edges_set_gt = load_edges(dep_gt_to_use)
edges_set_output = load_edges(dep_output_to_use)

# Load nodes
nodes_set_gt = load_nodes(edges_set_gt)
nodes_set_output = load_nodes(edges_set_output)

# TODO add fact visualisation
# fact = ground_truth['fact']['key'] if 'fact' in ground_truth else ''

# Visualisation

G = nx.DiGraph()

tp_color, fn_color, fp_color = 'green', 'grey', 'red'
dep_loop_color = 'yellow'

# Extract tables name to obtain short names
short_names = short_names_from_tables(edges_set_gt, edges_set_output)

# List of edges classified to color correctly
tp_edges_list, fn_edges_list, fp_edges_list = get_tp_fn_fp_edges_to_list(edges_set_gt, edges_set_output)

inserted_nodes = []

# Add nodes and edges from the dictionaries
for dep_list in [tp_edges_list, fn_edges_list, fp_edges_list]:
    for dep in dep_list:
        dep_dict = dict()
        color = tp_color if dep in tp_edges_list else fn_color if dep in fn_edges_list else fp_color if dep in fp_edges_list else \
            'black'
        for key, value in dep.items():
            dep_dict[key] = value

            value_preprocessed = preprocess_dependencies_attributes(value, input_config['visualisation']['table_names'], short_names)

            if value_preprocessed not in inserted_nodes:
                G.add_node(value_preprocessed, color=color)
                inserted_nodes.append(value_preprocessed)
            # If already present, in case of dependency in false positive (red one), if already considered
            # in false negative (grey), must be converted to true positive since it's been detected as
            # a dependency (green)
            else:
                if dep in fp_edges_list:
                    if value_preprocessed in nodes_set_gt:
                        G.nodes[value_preprocessed]['color'] = tp_color
        from_preprocessed = preprocess_dependencies_attributes(dep_dict['from'], input_config['visualisation']['table_names'], short_names)
        to_preprocessed = preprocess_dependencies_attributes(dep_dict['to'], input_config['visualisation']['table_names'], short_names)
        # If it's not auto dependency can be added
        if not input_config['visualisation']['dag_graph'] or from_preprocessed != to_preprocessed:
            G.add_edge(from_preprocessed, to_preprocessed, color=color)
        # Otherwise it's not added and color is changed to yellow, given that graph visualisation is based on DAG
        else:
            G.nodes[from_preprocessed]['color'] = dep_loop_color

arrow_size = input_config['visualisation']['arrow_size']

# if input_config['visualisation']['dag_graph']:
#     if not nx.is_directed_acyclic_graph(G):
#         raise Exception('Graph is not DAG, change visualisation')
#    pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
# else:
pos = nx.shell_layout(G)

plt.figure(figsize=(12, 8))

edge_colors = [G[u][v]['color'] for u, v in G.edges()] if input_config['visualisation']['edge_color'] else None
node_colors = [G.nodes[n]['color'] for n in G.nodes()] if input_config['visualisation']['node_color'] else None

# Draw nodes and edges
nx.draw(G, pos, edge_color=edge_colors, node_color=node_colors,
        with_labels=True, node_size=input_config['visualisation']['node_size'],
        font_size=input_config['visualisation']['font_size'], font_weight='bold', arrows=True, arrowsize=arrow_size)

# Draw edge labels
edge_labels = nx.get_edge_attributes(G, 'label')
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red')

if input_config['visualisation']['table_names']:
    legend_items = [plt.Line2D([0], [0], color='w', label=f'{full_name}: {short_name}')
                    for full_name, short_name in short_names.items()]
    for component in metrics:
        legend_items.append(mlines.Line2D([], [], color='black', linestyle='-', linewidth=2))
        legend_items.extend([plt.Line2D([0], [0], color='w', label=f'{component.capitalize()}:')])
        for sub_metrics in metrics[component]:
            legend_items.extend([plt.Line2D([0], [0], color='w', label=f'{sub_metrics}: {metrics[component][sub_metrics]}%')])
    plt.legend(handles=legend_items, title="Tables convention", fontsize='small', title_fontsize='medium',
               labelspacing=0.3, handletextpad=0.4, loc='upper left')

# Display the grap
plt.title("Graph Visualisation")

store_image(plt, ex_name, input_config['visualisation']['image']['format'])

if input_config['visualisation']['show_graph']:
    plt.show()
else:
    # Close the plot
    plt.close()