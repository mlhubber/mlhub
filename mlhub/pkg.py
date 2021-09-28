#!/usr/bin/python3
#
# mlhub - Machine Learning Model Repository
#
# A command line tool for managing machine learning models.
#
# Copyright 2018-2019 (c) Graham.Williams@togaware.com All rights reserved.
#
# This file is part of mlhub.
#
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the ""Software""), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import json
import os
import sys
import requests
import getpass
import subprocess
import re
import textwrap
from mlhub.utils import yes_or_no


# ----------------------------------------------------------------------
# Support Package Developers
# ----------------------------------------------------------------------
def load_key(path):
    """Load subscription key and endpoint from file."""
    key = None
    endpoint = None
    markchar = "'\" \t"
    with open(path, 'r') as file:
        for line in file:
            line = line.strip('\n')
            pair = line.split('=')
            if len(pair) == 2:
                k = pair[0].strip(markchar).lower()
                v = pair[1].strip(markchar)
                if k == 'key':
                    key = v
                elif k == 'endpoint':
                    endpoint = v
            elif not line.startswith('#'):
                line = line.strip(markchar)
                if line.startswith('http'):
                    endpoint = line
                else:
                    key = line
    return key, endpoint


def generalkey(key_file, priv_info, verbose=True, ask=True):
    """Load key, location, etc from file or ask user and save.

    The user is asked for an general key, location, etc.
     The provided information is saved into a file
    for future use. The contents of that file is the key.

    {"key":"abcd1234abcda4f2f6e9f565df34ef24","location":"eastaustralia"}

    """

    key = None

    # Set up messages.

    msg_request = """\
Private information is required to access this service.
See the README for more details.
"""

    msg_found = f"""\
The following file has been found and is assumed to
contain the private information.

    {key_file}"""

    msg_saved = """
That information has been saved into the file:

    {}""".format(key_file)

    # Obtain the key/location/etc.

    if os.path.isfile(key_file) and os.path.getsize(key_file) > 0:
        if verbose:
            print(msg_found, file=sys.stderr)

        if ask:
            yes = yes_or_no("\nUse this private information ('d' to "
                            "display, 'n' to update)", third_choice=True)
        else:
            yes = True

        if yes == "d":
            with open(key_file, 'r') as handle:
                parsed = json.load(handle)
            print(f"\n{json.dumps(parsed, indent=2)}")
            yes = yes_or_no("\nUse this private information (type 'n' to update)")

        if not yes:
            print("\n" + msg_request, file=sys.stderr)
            data = {}

            if any(isinstance(el, list) for el in priv_info):

                # private:
                #   Azure speech:key*, location
                # In this case, the priv_info = [[Azure speech, [key, location]]]

                for item in priv_info:
                    service = item[0]
                    nested_dic = {}

                    for elem in item[1]:
                        key_or_other = ask_info(elem, service)
                        nested_dic[elem] = key_or_other

                    data[service] = nested_dic

            # private:
            #   Azure speech:key*, location
            # In this case, the priv_info = [key, location]

            else:
                for item in priv_info:
                    key_or_other = ask_info(item,"")
                    data[item] = key_or_other

            # Write data into json file
            with open(key_file, "w") as outfile:
                json.dump(data, outfile)
            outfile.close()
            print(msg_saved, file=sys.stderr)


    else:
        print(msg_request, file=sys.stderr)

        if ask:
            data = {}

            if any(isinstance(el, list) for el in priv_info):

                # private:
                #   Azure speech:key*, location
                # In this case, the priv_info = [[Azure speech, [key, location]]]

                for item in priv_info:
                    service = item[0]
                    nested_dic = {}

                    for elem in item[1]:
                        key_or_other = ask_info(elem, service)
                        nested_dic[elem] = key_or_other

                    data[service] = nested_dic

            # private:
            #   Azure speech:key*, location
            # In this case, the priv_info = [key, location]

            else:
                for item in priv_info:
                    key_or_other = ask_info(item, "")
                    data[item] = key_or_other

            # Write data into json file
            with open(key_file, "w") as outfile:
                json.dump(data, outfile)
            outfile.close()
            print(msg_saved, file=sys.stderr)


def ask_info(item, service):
    if "*" in item:
        item = item.replace("*", "")
        key_or_other = ask_password(f"Please paste your {service} {item}: ")
    else:
        sys.stderr.write(f"Please paste your {item}: ")
        key_or_other = input()
    return key_or_other


def ask_password(prompt=None):
    if prompt is None:
        prompt = "Password: "
    return getpass.getpass(prompt=prompt)


# Send a request.


def azrequest(endpoint, url, subscription_key, request_data):
    """Send anomaly detection request to the Anomaly Detector API.

    If the request is successful, the JSON response is returned.

    Aim to generalise this to go into MLHUB to send request.
    """

    headers = {'Content-Type': 'application/json',
               'Ocp-Apim-Subscription-Key': subscription_key}

    response = requests.post(os.path.join(endpoint, url),
                             data=json.dumps(request_data),
                             headers=headers)

    if response.status_code == 200:
        return json.loads(response.content.decode("utf-8"))
    else:
        print(response.status_code)
        raise Exception(response.text)


def mlask(begin="", end="", prompt="Press Enter to continue"):
    begin = "\n" if begin else begin
    end = "\n" if end else end
    sys.stdout.write(begin + prompt + ": ")
    answer = input()
    sys.stdout.write(end)


def mlcat(title="", text="", delim="=", begin="", end="\n"):
    sep = delim * len(title) + "\n" if len(title) > 0 else ""
    ttl_sep = "\n" if len(title) > 0 else ""
    # Retain any extra line in the original text since fill() will
    # remove it.
    if len(text) and text[-1] == "\n": end = "\n" + end
    # Split into paragraphs, fill each paragraph, convert back to a
    # list of strings, and join them together as the text to be
    # printed.
    text = "\n\n".join(list(map(textwrap.fill, text.split("\n\n"))))
    print(begin + sep + title + ttl_sep + sep + ttl_sep + text, end=end)


def mlpreview(fname,
              begin="\n",
              msg="Close the graphic window using Ctrl-W.\n",
              previewer="eog"):
    print(begin + msg)
    subprocess.Popen([previewer, fname])


# From Simon Zhao's azface package on github.


def is_url(url):
    """Check if url is a valid URL."""

    urlregex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    if re.match(urlregex, url) is not None:
        return True
    else:
        return False


def get_cmd_cwd():
    """Return the dir where model pkg command is invoked.

    For example, if `cd /temp; ml demo xxx`, then get_cmd_cwd()
    returns `/temp`.  It is used by model pkg developer, and is
    different from where the model pkg script is located.

    `CMD_CWD` is a environment variable passed by
    mlhub.utils.dispatch() when invoke model pkg script.
    """

    return os.environ.get("_MLHUB_CMD_CWD", "")


def get_private(file_path="private.json", server=None):
    """Return a list of private information

    For example when call get_private()
    returns ["asdfghjkl", "westus"]. The first element is key,and the second
    is location. The order in the list is the same as the order in private
    row in MLHUB.yaml.
    If server is None, this function will return the first private information,
    otherwise it will return the specific one.

    """
    path = os.path.join(os.getcwd(), file_path)
    if os.path.exists(path):
        with open(path) as f:
            private_info = json.load(f)
            values = list(private_info.values())

            # The MLHub yaml includes
            #
            # private:
            #   Azure Speech: key*, location

            if any(isinstance(el, dict) for el in values):
                for item in values:
                    for i in list(item.values()):
                        if i == "":
                            sys.exit("Your private information is blank. "
                                     "Please run ml configure <model> to paste your private information.")
                print(server)
                if server is None:
                    return list(values[0].values())
                else:
                    if server in list(private_info.keys()):
                        return list(private_info[server].values())
                    else:
                        sys.exit("The server's name doesn't exist.\n"
                                 "Please make sure you have the correct name.")

            # private:key*, location
            # In this case, the values = [asdfghj(key), australia(location)]

            else:
                for item in values:
                    if item == "":
                        sys.exit("Your private information is blank. "
                                 "Please run ml configure <model> to paste your private information.")
                return values

    else:
        sys.exit("Please run ml configure <model> to paste your private information.")
