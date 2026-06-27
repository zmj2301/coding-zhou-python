import json
import os
current_script_dir = os.path.dirname(os.path.abspath(__file__))

level_progress = [False]*10

with open(current_script_dir+'/user_data_test.json', 'w') as f:
    json.dump(level_progress, f, indent=4)

with open(current_script_dir+'/user_data_test.json', 'r') as f:
    data = json.load(f)
    print(data,type(data))
