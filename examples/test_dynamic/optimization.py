
#%%
import itertools

import os

def generate_flags_combinations(length):
    return itertools.product([0, 1], repeat=length)

def run_simulation_and_save_output(flags, output_filename):
    flags_str = " ".join(map(str, flags))  # Convert flags list to a comma-separated string
    # Construct the command, assuming your script can directly interpret the list format for flags
    command = f'python test.py --flags {flags_str}'
    os.system(command)
#%%
flag_combinations = generate_flags_combinations(4)  # Assuming you are working with 4 flags
result_files = []

for i, flags in enumerate(flag_combinations):
    output_filename = f'results_{i}.txt'  # Unique filename for each simulation's output
    run_simulation_and_save_output(flags, output_filename)
    result_files.append(output_filename)

# After running all simulations, analyze results
# You will need to define how you want to analyze the results
# For example, by reading each file and checking some performance metric
# for filename in result_files:
#     # Implement your analysis logic here
#     pass



# %%
