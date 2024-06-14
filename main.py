##### Imports #####
import re
import sys
import os
import json
import requests
from distutils.util import strtobool
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import pprint

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

def get_paginated_data(url):
    data = []

    auth_headers = {"Authorization": f"token {github_token}"}
    try:
        session = requests.Session()
        retries = Retry(total=10, backoff_factor=1, status_forcelist=[ 404, 429, 500, 502, 503, 504 ])
        session.mount('https://', HTTPAdapter(max_retries=retries))

        resp = session.get(url, headers=auth_headers)
        if resp.status_code == 200:
            data += resp.json()

            # Check if the request was paginated (it will contain a Link header)
            # python requests already parses this header under the attribute links
            if resp.links:
                if "next" in resp.links:
                    next_page_url = resp.links['next']['url']
                    while True:
                        resp_page = session.get(next_page_url, headers=auth_headers)
                        if resp_page.status_code == 200:
                            data += resp_page.json()

                            # Check if there is a new next page url
                            if resp_page.links:
                                if "next" in resp_page.links:
                                    next_page_url = resp_page.links['next']['url']
                                else:
                                    # There was no next page
                                    break
                        else:
                            # We didn't get a successful response, bail out of the infinite loop
                            # TBD: if we should just throw an exception in this case instead
                            # raise SystemExit(f"Recieved unexpected response code: {resp.status_code} from the Github REST API!")
                            break
        else:
            raise SystemExit(f"Recieved unexpected response code: {resp.status_code} from the Github REST API!")
    except:
        raise SystemExit(f"Could not talk to the Github API, gave up after 10 retries! {sys.exc_info()}")

    return data

def check_files_and_folders(pull_request_url):
    valid = True
    # To get the changed files, append "/files" to the pull request url, there doesn't seem to be
    # any references to it from the pull request event data, the list of files changes, could likely
    # be paginated, so make sure to check for that
    
    if "url" in pull_request_url:
        data = get_paginated_data(f"{pull_request_url['url']}/files")
       
        for file_changed in data:
            # We only care about files being added or modified
            if ("status" in file_changed) and ("filename" in file_changed):
                if file_changed["status"].lower() == "modified" or file_changed["status"].lower() == "added":
                    
                    filename = file_changed["filename"]
                    basename = os.path.basename(filename)
                    foldername = os.path.dirname(filename)

                    if require_lowercase_files:
                        # Check if its a excluded file
                        if basename not in excluded_files:
                            if not basename.islower():
                                # Print whole path for easier debugging
                                print(f"File breaking the policy: {filename}")
                                valid = False
                    
                    if require_lowercase_folders:
                        # The foldername might be empty, if it was a file in the root of the repo
                        if len(foldername) >0:
                            if foldername not in excluded_folders:
                                if not foldername.islower():
                                    print(f"Folder breaking the policy: {foldername}")
                                    valid = False
            else:
                raise SystemExit('Did not find the expected element: status in the JSON response')

    else:
        raise SystemExit('Did not find the expected element: url in the pull request event data')
    
    return valid
    
##### Main #####
if __name__ == '__main__':

    pull_request_json = get_pull_request_json()

    if check_files_and_folders(pull_request_json):
        sys.exit(0)
    else:
        raise SystemExit('You need to fix the case of your files/folders to match the naming standard')


