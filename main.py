##### Imports #####
import re
import sys
import os
import json
import requests
from distutils.util import strtobool
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Expected script args:
# sys.argv[1] - Require lower case files (bool)
# sys.argv[2] - Require lower case folders (bool)
# sys.argv[3] - Excluded files (JSON list)
# sys.argv[5] - Excluded folders (JSON list)
# sys.argv[7] - Github token (string)

##### Helper functions #####
def to_json_list(input_string):
    try:
        return json.loads(input_string)
    except:
        return json.loads('[]') # Should not happen really if the input was valid

# Check if the argument exists, (and convert them to Python booleans etc), 
# if they are not present, then set them to some sane defaults
require_lowercase_files = bool(strtobool(sys.argv[1])) if len(sys.argv) >= 2 else True
require_lowercase_folders = bool(strtobool(sys.argv[2])) if len(sys.argv) >= 3 else True
excluded_files = to_json_list(sys.argv[3]) if len(sys.argv) >= 4 else to_json_list('[]')
excluded_folders = to_json_list(sys.argv[4]) if len(sys.argv) >= 5 else to_json_list('[]')
github_token = sys.argv[5] if len(sys.argv) >= 6 else None
# print(f"DEBUG - Excluded files: {excluded_files}")
# print(f"DEBUG - Excluded folders: {excluded_files}")

##### Functions #####
def get_pull_request_json():
    try:
        # Try to open the event file (json) that is specified with the environment
        # varible: GITHUB_EVENT_PATH, this will contain the pull request details
        # but it will not list each individual commit message, for that we need to
        # use the python github client, with required the GITHUB_TOKEN to work.

        # Check if the GITHUB_EVENT_PATH environment variable has been set
        if "GITHUB_EVENT_PATH" in os.environ:

            # Open the event json file, and parse it with json
            with open(os.environ['GITHUB_EVENT_PATH'], 'r') as event_file:
                event_data = json.load(event_file)
                
                # Check that we are actually running on a pull request status check
                if "pull_request" in event_data:
                    return event_data['pull_request']
                else:
                    raise SystemExit('There was no pull request data in the triggered event!')
        else:
            raise SystemExit('Missing the GITHUB_EVENT_PATH environment variable!')
    except:
        raise SystemExit('Unable to parse the pull request!')

##### Main #####
if __name__ == '__main__':
    valid_pull_request = True # Assume true, unless checks fail

    pull_request_json = get_pull_request_json()

    
