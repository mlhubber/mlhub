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


def azkey(key_file, service="Cognitive Services", connect="endpoint",
          verbose=True, baseurl=False):
    """Load key and endpoint/location from file or ask user and save. 

    The user is asked for an Azure subscription key and
    endpoint/location. The provided information is saved into a file
    for future use. The contents of that file is the key and
    endpoint/location with the endpoint identified as starting with
    http. Some endpoints may include the full cognitive service path
    and so the baseurl option will strip to just the base name of the
    URL.

    abcd1234abcda4f2f6e9f565df34ef24
    https://westus2.api.cognitive.microsoft.com

    OR

    abcd1234abcda4f2f6e9f565df34ef24
    https://westus2

    """

    key = None

    # Set up messages.
    
    prompt_key = f"Please paste your {service} subscription key: "
    prompt_endpoint = f"Please paste your {connect}: "

    msg_request = f"""\
An Azure resource is required to access this service (and to run this command).
See the README for details of a free subscription. If you have a subscription
then please paste the key and the {connect} here.
"""
    msg_found = f"""\
The following file has been found and is assumed to contain an Azure 
subscription key and {connect} for {service}. We will load 
the file and use this information.

    {key_file}
"""

    msg_saved = """
That information has been saved into the file:

    {}
""".format(key_file)

    # Obtain the key/connect.

    if os.path.isfile(key_file) and os.path.getsize(key_file) > 0:
        if verbose: print(msg_found, file=sys.stderr)
        key, endpoint = load_key(key_file)
    else:
        print(msg_request, file=sys.stderr)
        
        key      = ask_password(prompt_key)
        sys.stderr.write(prompt_endpoint)
        endpoint = input()

        if len(key) > 0 and len(endpoint) > 0:
            ofname = open(key_file, "w")
            # Use the explicit format in case endpoint has no http prefix.
            ofname.write("key={}\nendpoint={}\n".format(key, endpoint))
            ofname.close()
            print(msg_saved, file=sys.stderr)

    if baseurl:
        from urllib.parse import urlsplit
        splurl = urlsplit(endpoint)
        endpoint = splurl.scheme + "://" + splurl.netloc

    # Ensure endpoint ends in /

    if endpoint[-1] == "/":
        if connect == "location": endpoint = endpoint[:-1]
    else:
        if connect == "endpoint": endpoint = endpoint + "/"
        
    return key, endpoint

# Simple input of password.


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

    Aim to generailse this to go into MLHUB to send request.
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
    sep = delim*len(title) + "\n" if len(title) > 0 else ""
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
