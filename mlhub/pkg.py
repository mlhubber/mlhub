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
import termios
import tty
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


def generalkey(key_file, service, require_info, verbose=True, ask=True):
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
See the README for more details."""

    msg_found = f"""\
The following file has been found and is assumed to
contain the private information for {service}.

    {key_file}"""

    msg_saved = """
That information has been saved into the file:

    {}""".format(key_file)

    # Obtain the key/location/etc.

    if os.path.isfile(key_file) and os.path.getsize(key_file) > 0:
        if verbose:
            print(msg_found, file=sys.stderr)

        if ask:
            yes = yes_or_no("\nUse this private information (type 'n' to update)")
        else:
            yes = True

        if not yes:
            print("\n" + msg_request, file=sys.stderr)
            data = {}
            for item in require_info:

                if "*" in item:
                    message_key = item.replace("*", "")
                    key = ask_password(f"\nPlease paste your {service} {message_key}: ")
                    if len(key) > 0:
                        js_key = message_key.replace(" ", "_")
                        data[js_key] = key
                else:
                    js_key = item.replace(" ", "_")
                    sys.stderr.write(f"Please paste your {service} {item}: ")
                    other = input()
                    data[js_key] = other

            # Write data into json file
            with open(key_file, "w") as outfile:
                json.dump(data, outfile)
            outfile.close()
            print(msg_saved, file=sys.stderr)

    else:
        print(msg_request, file=sys.stderr)

        if ask:
            data = {}
            for item in require_info:

                if "*" in item:
                    message_key = item.replace("*", "")
                    key = ask_password(f"\nPlease paste your {service} {message_key}: ")
                    if len(key) > 0:
                        js_key = message_key.replace(" ", "_")
                        data[js_key] = key
                else:
                    js_key = item.replace(" ", "_")
                    sys.stderr.write(f"Please paste your {item}: ")
                    other = input()
                    data[js_key] = other

            # Write data into json file
            with open(key_file, "w") as outfile:
                json.dump(data, outfile)
            outfile.close()
            print(msg_saved, file=sys.stderr)


def ask_password(prompt=None):
    """Echo '*' for every input character. Only implements the basic I/O
    functionality and so only Backspace is supported.  No support for
    Delete, Left key, Right key and any other line editing.

    Reference: https://mail.python.org/pipermail/python-list/2011-December/615955.html
    """

    symbol = "`~!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?"
    if prompt:
        sys.stderr.write(prompt)
        sys.stderr.flush()

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    chars = []
    try:
        tty.setraw(sys.stdin.fileno())
        while True:
            c = sys.stdin.read(1)
            if c in '\n\r':  # Enter.
                break
            if c == '\003':
                raise KeyboardInterrupt
            if c == '\x7f':  # Backspace.
                if chars:
                    sys.stderr.write('\b \b')
                    sys.stderr.flush()
                    del chars[-1]
                continue
            if c.isalnum() or c in symbol:
                sys.stderr.write('*')
                sys.stderr.flush()
                chars.append(c)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        sys.stderr.write('\n')

    return ''.join(chars)


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
