#!/usr/bin/python3
#
# mlhub - Machine Learning Model Repository
#
# A command line tool for managing machine learning models.
#
# Copyright 2018 (c) Graham.Williams@togaware.com All rights reserved. 
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

import base64
import cgi
import distro
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import yaml
import yamlordereddictloader
import zipfile
import tarfile

from mlhub.constants import (
    APP,
    APPX,
    CACHE_DIR,
    CMD,
    COMMANDS,
    COMPLETION_DIR,
    DESC_YAML,
    DESC_YML,
    EXT_AIPK,
    EXT_MLM,
    LOG_DIR,
    META_YAML,
    META_YML,
    MLHUB,
    MLHUB_YAML,
    MLINIT,
    TMP_DIR,
    USAGE,
    VERSION,
)


def print_usage():
    print(CMD)
    print(USAGE.format(CMD, MLHUB, MLINIT, VERSION, APP))


def _create_dir(path, error_msg, exception):
    """Check if the dir exists and if not then create it.

    Args:
        path (str): the dir path.
        error_msg (str): log error message if mkdir fails.
        exception (Exception): The exception raised when error.
    """

    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except OSError:
        logger = logging.getLogger(__name__)
        logger.error(error_msg, exc_info=True)
        raise exception

    return path


def create_init():
    """Check if the init dir exists and if not then create it."""

    return _create_dir(
        MLINIT,
        'MLINIT creation failed: {}'.format(MLINIT),
        MLInitCreateException(MLINIT)
    )


def create_mlhubtmpdir():
    """Check if the tmp dir exists and if not then create it."""

    return _create_dir(
        TMP_DIR,
        'TMP_DIR creation failed: {}'.format(TMP_DIR),
        MLTmpDirCreateException(TMP_DIR)
    )


def get_repo(repo):
    """Determine the repository to use: command line, environment, default."""

    if repo is None:
        repo = MLHUB
    else:
        repo = os.path.join(repo, "")  # Ensure trailing slash.

    return repo


def get_repo_meta_data(repo):
    """Read the repositories meta data file and return as a list."""

    try:
        url = repo + META_YAML
        meta = list(yaml.load_all(urllib.request.urlopen(url).read()))
    except urllib.error.URLError:
        try: 
            url = repo + META_YML
            meta = list(yaml.load_all(urllib.request.urlopen(url).read()))
        except urllib.error.URLError:
            logger = logging.getLogger(__name__)
            logger.error('Repo connection problem.', exc_info=True)
            raise RepoAccessException(repo)

    return meta


def print_meta_line(entry):
    name = entry["meta"]["name"]
    version = entry["meta"]["version"]
    try:
        title = entry["meta"]["title"]
    except KeyError:
        title = entry["meta"]["description"]

    # One line message.

    max_title = 24
    max_descr = 44
    
    if len(title) > max_descr:
        long = "..."
    else:
        long = ""

    formatter = "{0:<TITLE.TITLE} {1:^6} {2:<DESCR.DESCR}{3}".\
        replace("TITLE", str(max_title)).replace("DESCR", str(max_descr))
    print(formatter.format(name, version, title, long))


def get_version(model=None):
    if model is None:
        return VERSION
    else:
        entry = load_description(model)
        return entry["meta"]["version"]


def print_model_cmd_help(info, cmd):
    print("\n  $ {} {} {}".format(CMD, cmd, info["meta"]["name"]))

    c_meta = info['commands'][cmd]
    if type(c_meta) is str:
        print("    " + c_meta)
    else:
        # Handle malformed DESCRIPTION.yaml like
        # --
        # commands:
        #   print:
        #     description: print a textual summary of the model
        #   score:
        #     equired: the name of a CSV file containing a header and 6 columns
        #     description: apply the model to a supplied dataset

        desc = c_meta.get('description', None)
        if desc is not None:
            print("    " + desc)

        c_meta = {k: c_meta[k] for k in c_meta if k != 'description'}
        if len(c_meta) > 0:
            msg = yaml.dump(c_meta, default_flow_style=False)
            msg = msg.split('\n')
            msg = ["    " + ele for ele in msg]
            print('\n'.join(msg), end='')


def check_model_installed(model):
    """Check if model installed."""

    path = MLINIT + model

    logger = logging.getLogger(__name__)
    logger.debug("Check if package {} is installed at: {}".format(model, path))

    if not os.path.exists(path):
        raise ModelNotInstalledException(model)

    return True


def load_description(model):
    """Load description of the <model>."""

    try:
        desc = get_available_pkgyaml(os.path.join(MLINIT, model))
        entry = read_mlhubyaml(desc)
    except DescriptionYAMLNotFoundException:
        raise DescriptionYAMLNotFoundException(model)

    return entry


def read_mlhubyaml(name):
    """Read description from a specified local yaml file or the url of a yaml file."""

    try:
        if is_github_url(name):
            res = json.loads(urllib.request.urlopen(name).read())
            content = base64.b64decode(res["content"])
        elif is_url(name):
            content = urllib.request.urlopen(name).read()
        else:
            content = open(name)

        entry = yaml.load(content, Loader=yamlordereddictloader.Loader)
    except (yaml.composer.ComposerError, yaml.scanner.ScannerError):
        raise MalformedYAMLException(name)
    except urllib.error.URLError:
        raise YAMLFileAccessException(name)

    return entry


def configure(path, script, quiet):
    """Run the provided configure scripts and handle errors and output."""

    configured = False
    
    # For now only tested/working with Ubuntu
    
    if distro.id() in ['debian', 'ubuntu']:
        conf = os.path.join(path, script)
        if os.path.exists(conf):
            interp = interpreter(script)
            if not quiet:
                msg = "Configuring using '{}'...\n".format(conf)
                print(msg)
            cmd = "export _MLHUB_CMD_CWD='{}'; export _MLHUB_MODEL_NAME='{}'; {} {}".format(
                os.getcwd(), os.path.basename(path), interp, script)
            logger = logging.getLogger(__name__)
            logger.debug("(cd " + path + "; " + cmd + ")")
            proc = subprocess.Popen(cmd, shell=True, cwd=path, stderr=subprocess.PIPE)
            output, errors = proc.communicate()
            if proc.returncode != 0:
                errors = errors.decode("utf-8")
                logger.error("Configure failed: \n{}".format(errors))
                print("An error was encountered:\n")
                print(errors)
                raise ConfigureFailedException()
            configured = True

    return configured


def flatten_mlhubyaml_deps(deps, cats=None, res=[]):
    """Flatten the hierarchical structure of dependencies in MLHUB.yaml.

    For dependency specification like:

      dependencies:
        system: atril
        R:
          cran: magrittr, dplyr=1.2.3, caret>4.5.6, e1017, httr  # All dependencies in one line
          github:  # One dependency per line
            - rstudio/tfruns
            - rstudio/reticulate
            - rstudio/keras
        python:
          conda: environment.yaml  # Use conda to interpret dependencies
          pip:
            - pillow
            - tools=1.1
        files:
          - https://github.com/mlhubber/colorize/raw/master/configure.sh
          - https://github.com/mlhubber/colorize/raw/master/configure.sh: data/
          - https://github.com/mlhubber/colorize/raw/master/configure.sh: images/cat.png
          - https://github.com/mlhubber/colorize/archive/master.zip: res/
          - https://github.com/mlhubber/colorize/archive/master.zip: res/xyz.zip

    Return something like:

      [[['system'], ['atril']],
       [['r', 'cran'], ['magrittr', 'dplyr=1.2.3', 'caret>4.5.6', 'e1017', 'httr']],
       [['r', 'github'], ['rstudio/tfruns', 'rstudio/reticulate', 'rstudio/keras']],
       [['python', 'conda'], ['environment.yaml']],
       [['python', 'pip'], ['pillow', 'tools=1.1']],
       [['files'], {'https://github.com/mlhubber/colorize/raw/master/configure.sh': None,
                    'https://github.com/mlhubber/colorize/raw/master/configure.sh': 'data/',
                    'https://github.com/mlhubber/colorize/raw/master/configure.sh': 'images/cat.png',
                    'https://github.com/mlhubber/colorize/archive/master.zip': 'res/',
                    'https://github.com/mlhubber/colorize/archive/master.zip': 'res/xyz.zip'}]
      ]
    """

    def _dep_split(deps_spec):
        return [x.strip() for x in deps_spec.split(',')]

    def _get_file_target_dict(dep_list):
        res = {}
        for dep in dep_list:
            if isinstance(dep, str):
                res[dep] = None
            else:
                res.update(dep)
        return res

    if not isinstance(deps, dict):

        if isinstance(deps, str):
            deps = _dep_split(deps)

        res.append([[cats] if cats is None else cats, deps])

    else:

        for category in deps:
            if 'files'.startswith(category):
                if isinstance(deps[category], str):
                    dep_dict = _get_file_target_dict(_dep_split(deps[category]))
                else:
                    dep_dict = _get_file_target_dict(deps[category])
                res.append([['files'], dep_dict])
            else:
                cat_list = [category.lower()] if cats is None else cats + [category.lower()]
                flatten_mlhubyaml_deps(deps[category], cat_list, res)

    return res


def install_r_deps(deps, model, source='cran'):
    script = os.path.join(os.path.dirname(__file__), 'scripts', 'dep', 'r.R')
    command = 'Rscript {} "{}" "{}"'.format(script, source, '" "'.join(deps))

    proc = subprocess.Popen(command, shell=True, cwd=get_package_dir(model), stderr=subprocess.PIPE)
    output, errors = proc.communicate()
    if proc.returncode != 0:
        errors = errors.decode("utf-8")
        print("An error was encountered:\n")
        print(errors)
        raise ConfigureFailedException()


def install_python_deps(deps, source='pip'):
    script = os.path.join(os.path.dirname(__file__), 'scripts', 'dep', 'python.sh')
    command = 'bash {} "{}" "{}"'.format(script, source, '" "'.join(deps))

    proc = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE)
    output, errors = proc.communicate()
    if proc.returncode != 0:
        errors = errors.decode("utf-8")
        print("An error was encountered:\n")
        print(errors)
        raise ConfigureFailedException()


def install_system_deps(deps):
    script = os.path.join(os.path.dirname(__file__), 'scripts', 'dep', 'system.sh')
    command = 'bash {} "{}"'.format(script, '" "'.join(deps))

    proc = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE)
    output, errors = proc.communicate()
    if proc.returncode != 0:
        errors = errors.decode("utf-8")
        print("An error was encountered:\n")
        print(errors)
        raise ConfigureFailedException()


def get_url_filename(url):
    """Obtain the file name from URL."""

    info = urllib.request.urlopen(url).getheader('Content-Disposition')
    if info is None:  # File name can be obtained from URL per se.
        filename = os.path.basename(url)
    else:  # File name may be obtained from 'Content-Dispositon'.
        _, params = cgi.parse_header(info)
        filename = params['filename']

    return filename


def install_file_deps(deps, model):

    # TODO: Add download progress indicator, or use wget --quiet --show-progress <url> 2>&1

    # Download file into Cache dir, then symbolically link it into Package dir.
    # Thus we can reuse the downloaded files after model package upgrade.
    # If a lot of files are downloaeded into the same dir,
    # then only the link of their top parent dir is enough.

    # For example, if MLHUB.yaml is
    #   files:
    #     - https://zzz.org/label
    #     - https://zzz.org/cat.RData: data/
    #     - https://zzz.org/def.RData: data/dog.RData
    #     - https://zzz.org/xyz.zip:   res/
    #     - https://zzz.org/z.zip:   ./
    #
    # Then the directory structure will be:
    #   In cache dir:
    #     ~/.mlhub/.cache/<pkg>/label
    #     ~/.mlhub/.cache/<pkg>/data/cat.RData
    #     ~/.mlhub/.cache/<pkg>/data/dog.RData
    #     ~/.mlhub/.cache/<pkg>/res/<files-inside-xyz.zip>
    #     ~/.mlhub/.cache/<pkg>/<files-inside-z.zip>
    #
    #   In Package dir:
    #     ~/.mlhub/<pkg>/label                  ---link-to-->   ~/.mlhub/.cache/<pkg>/label
    #     ~/.mlhub/<pkg>/data                   ---link-to-->   ~/.mlhub/.cache/<pkg>/data
    #     ~/.mlhub/<pkg>/res                    ---link-to-->   ~/.mlhub/.cache/<pkg>/res
    #     ~/.mlhub/<pkg>/<files-inside-z.zip>   ---link-to-->   ~/.mlhub/.cache/<pkg>/<files-inside-z.zip>

    print("\nDownloading required files ...")

    cache_dir = create_package_cache_dir(model)
    pkg_dir = get_package_dir(model)
    mlhubtmp_dir = create_mlhubtmpdir()

    logger = logging.getLogger(__name__)
    logger.debug("deps: {}".format(deps))

    def link_cache_to_pkg(cache, target):
        """Link cache to a relative target under package directory.

        Args:
            cache (str): The absolute path of cached file.
            target (str): The relative path to the package dir.
        """

        segs = target.split(os.path.sep)
        if len(segs) > 1:
            top_dir = segs[0]
        else:
            top_dir = ''
        top_dir_src = os.path.join(cache_dir, top_dir)
        top_dir_dst = os.path.join(pkg_dir, top_dir)

        logger.debug("top_dir: {}".format(top_dir))
        logger.debug("top_dir_src: {}".format(top_dir_src))
        logger.debug("top_dir_dst: {}".format(top_dir_dst))

        if top_dir != '':  # File under a sub dir.  Make a link to its top dir if not exists.

            src = top_dir_src
            dst = top_dir_dst

            logger.debug("Link dir.")
            logger.debug("src: {}".format(src))
            logger.debug("dst: {}".format(dst))

            if os.path.exists(dst) and not os.path.islink(dst):
                remove_file_or_dir(dst)

            if not os.path.exists(dst):
                os.symlink(src, dst)

        else:  # File at the top level.  Make a link directly.

            src = cache
            dst = os.path.join(pkg_dir, target)

            logger.debug("Link file.")
            logger.debug("src: {}".format(src))
            logger.debug("dst: {}".format(dst))

            remove_file_or_dir(dst)
            os.symlink(src, dst)

    for url, target in deps.items():

        # Obtain file name from URL.

        filename = get_url_filename(url)

        # Download and install file.

        if target is None:  # Download to the top level dir without changing its name.
            target = filename

        if target.endswith(os.path.sep):
            target = os.path.relpath(target) + os.path.sep
        else:
            target = os.path.relpath(target)

        target_name = os.path.basename(target)
        cache = os.path.join(cache_dir, target)

        logger.debug("url: {}".format(url))
        logger.debug("target: {}".format(target))
        logger.debug("target_name: {}".format(target_name))

        msg = '\n  from {}\n  into {} ...'
        if target_name == '' and (is_mlm_zip(filename) or is_tar(filename)):  # Uncompress zip file

            print(msg.format(url, target))
            temp_file = os.path.join(mlhubtmp_dir, filename)
            urllib.request.urlretrieve(url, temp_file)
            _, _, file_list = unpack_with_promote(temp_file, cache, remove_dst=False)

            for file in file_list:
                link_cache_to_pkg(os.path.join(cache, file), os.path.join(target, file))

        else:

            if target_name == '':  # Download to a directory without changing name
                cache = os.path.join(cache, filename)
                target = os.path.join(target, filename)

            print(msg.format(url, target))
            logger.debug("cache: {}".format(cache))

            os.makedirs(os.path.dirname(cache), exist_ok=True)
            urllib.request.urlretrieve(url, cache)
            link_cache_to_pkg(cache, target)


def interpreter(script):
    """Determine the correct interpreter for the given script name."""
    
    (root, ext) = os.path.splitext(script)
    ext = ext.strip()
    if ext == ".sh":
        intrprt = "bash"
    elif ext == ".R":
        intrprt = "R_LIBS=./R Rscript"
    elif ext == ".py":
        intrprt = "python3"
    else:
        raise UnsupportedScriptExtensionException(ext)

    return intrprt


def dropdot(sentence):
    """Drop the period after a sentence."""
    return re.sub(".$", "", sentence)


def drop_newline(paragraph):
    """Drop trailing newlines."""

    return re.sub("\n$", "", paragraph)


def lower_first_letter(sentence):
    """Lowercase the first letter of a sentence."""

    return sentence[:1].lower() + sentence[1:] if sentence else ''


def get_command_suggestion(cmd, description=None, model=''):
    """Return suggestion about how to use the cmd."""

    if cmd in COMMANDS:
        meta = COMMANDS[cmd]

        # If there is customized suggestion, use it; otherwise
        # generate from description.

        if 'argument' in meta and 'model' in meta['argument'] and model == '':
            model = '<model>'

        msg = meta.get('suggestion',
                       "\nTo " + dropdot(lower_first_letter(meta['description'])) + ":"
                        "\n\n  $ {} {} {}")
        msg = msg.format(CMD, cmd, model)
        return msg

    elif description is not None:
        meta = description['commands'][cmd]

        if type(meta) is str:
            msg = dropdot(lower_first_letter(meta))
        else:
            # Handle malformed DESCRIPTION.yaml like
            # --
            # commands:
            #   print:
            #     description: print a textual summary of the model
            #   score:
            #     required: the name of a CSV file containing a header and 6 columns
            #     description: apply the model to a supplied dataset

            msg = meta.pop('description', None)

        if msg is not None:
            msg = "\nTo " + msg
        else:
            msg = "\nYou may try"
        msg += ":\n\n  $ {} {} {}"
        msg = msg.format(CMD, cmd, model)

        return msg


def print_commands_suggestions_on_stderr(*commands):
    """Print list of suggestions on how to use the command in commands."""

    for cmd in commands:
        print_on_stderr(get_command_suggestion(cmd))

    print_on_stderr('')


def print_next_step(current, description=None, scenario=None, model=''):
    """Print next step suggestions for the command.

    Args:
        current (str): the command needs to be given next step suggestion.
        description(dict): yaml object from DESCRIPTION.yaml
        scenario (str): certain scenario for the next step.
        model (str): the model name if needed.
    """

    if description is None:

        # Use the order for basic commands

        if 'next' not in COMMANDS[current]:
            return

        steps = COMMANDS[current]['next']

        if scenario is not None:
            steps = steps[scenario]

        for next_cmd in steps:
            msg = get_command_suggestion(next_cmd, model=model)
            print(msg)
    else:

        # Use the order in DESCRIPTION.yaml

        avail_cmds = list(description['commands'])

        try:
            next_index = avail_cmds.index(current) + 1 if current != 'commands' else 0
        except ValueError:
            # The command is not described in DESCRIPTION.yaml, ignore it.
            next_index = len(avail_cmds)

        if next_index < len(avail_cmds):
            next_cmd = avail_cmds[next_index]

            msg = get_command_suggestion(next_cmd, description=description, model=model)
        else:
            msg = "\nThank you for exploring the '{}' model.".format(model)

        print(msg)

    print()


def interpret_mlm_name(mlm):
    """Interpret model package file name into model name and version number.

    Args:
        mlm (str): mlm file path or url.

    Returns:
        file name, model name, version number.
    """

    if not ends_with_mlm(mlm):
        raise MalformedMLMFileNameException(mlm)

    mlmfile = os.path.basename(mlm)
    try:
        model, version = mlmfile.split('_')
    except ValueError:
        raise MalformedMLMFileNameException(mlm)

    version = '.'.join(version.split('.')[: -1])

    return model, version


def interpret_github_url(url):
    """Interpret GitHub URL into user name, repo name, branch/blob name.

    The URL may be:

              For master:  mlhubber/mlhub
              For branch:  mlhubber/mlhub@dev
              For commit:  mlhubber/mlhub@7fad23bdfdfjk
        For pull request:  mlhubber/mlhub#15

    Support for URL like https://github.com/... would not be portable.
    We just leave it in case someone doesn't know how to use Git refs.

              For master:  https://github.com/mlhubber/mlhub
          For repo clone:  https://github.com/mlhubber/mlhub.git
              For branch:  https://github.com/mlhubber/mlhub/tree/dev
             For archive:  https://github.com/mlhubber/mlhub/archive/v2.0.0.zip
                           https://github.com/mlhubber/mlhub/archive/dev.zip
              For a file:  https://github.com/mlhubber/mlhub/blob/dev/DESCRIPTION.yaml
        For pull request:  https://github.com/mlhubber/mlhub/pull/15
    """
    seg = url.split('/')
    ref = 'master'  # Use master by default.

    if not is_url(url):  #

        owner = seg[0]
        repo = seg[1]
        if '@' in seg[1]:

            # For branch or commit such as:
            #     mlhubber/mlhub@dev
            #     mlhubber/mlhub@7fad23bdfdfjk

            tmp = seg[1].split('@')
            repo = tmp[0]
            ref = tmp[1]

        elif '#' in seg[1]:

            # For pull request such as:
            #     mlhubber/mlhub#15

            tmp = seg[1].split('#')
            repo = tmp[0]
            ref = "pull/" + tmp[1] + "/head"

    else:

        owner = seg[3]
        repo = seg[4]
        if repo.endswith(".git"):  # Repo clone url
            repo = repo[:-4]

        if len(seg) >= 7:
            if len(seg) == 7:
                if seg[5] == "archive" and seg[6].endswith(".zip"):  # Archive url
                    ref = seg[6][:-4]
                elif seg[5] == "pull":  # Pull request url
                    ref = "pull/" + seg[6] + "/head"

            else:  # Branch, commit, or specific file
                ref = seg[6]

    return owner, repo, ref


def get_pkgzip_github_url(url):
    """Get the GitHub zip file url of model package.

    See https://developer.github.com/v3/repos/contents/#get-archive-link
    """

    owner, repo, ref = interpret_github_url(url)
    return "https://api.github.com/repos/{}/{}/zipball/{}".format(owner, repo, ref)


def get_pkgyaml_github_url(url):
    """Get the GitHub url of DESCRIPTION.yaml file of model package.

    See https://developer.github.com/v3/repos/contents/#get-contents
    """

    owner, repo, ref = interpret_github_url(url)
    url = "https://api.github.com/repos/{}/{}/contents/{{}}?ref={}".format(owner, repo, ref)
    return get_available_pkgyaml(url)


def get_available_pkgyaml(url):
    """Return the available package yaml file path.

    Possible options are MLHUB.yaml and DESCRIPTION.yaml.  If both exist, MLHUB.yaml takes precedence.
    Path can be a path to the package directory or a URL to the top level of the pacakge repo
    """
    yaml_list = [MLHUB_YAML, DESC_YAML, DESC_YML]

    if is_github_url(url):
        yaml_list = [url.format(x) for x in yaml_list]
    elif is_url(url):
        yaml_list = ['/'.join([url, x]) for x in yaml_list]
    else:
        yaml_list = [os.path.join(url, x) for x in yaml_list]

    if is_url(url):
        for x in yaml_list:
            try:
                if urllib.request.urlopen(x).status == 200:
                    return x
            except urllib.error.URLError:
                continue
    else:
        for x in yaml_list:
            if os.path.exists(x):
                return x

    raise DescriptionYAMLNotFoundException(url)


def download_model_pkg(url, local, quiet):
    """Download the model package mlm or zip file from <url> to <local>."""

    pkgfile = os.path.basename(url)
    if not quiet:
        print("Package " + url + "\n")

    meta = urllib.request.urlopen(url)
    if meta.status != 200:
        raise ModelURLAccessException(url)

    # Content-Length is not always necessarily available.

    dsize = meta.getheader("Content-Length")
    if dsize is not None:
        dsize = "{:,}".format(int(dsize))
        if not quiet:
            print("Downloading '{}' ({} bytes) ...\n".format(pkgfile, dsize))

    # Download the archive from the URL.

    try:
        urllib.request.urlretrieve(url, local)
    except urllib.error.URLError as error:
        raise ModelDownloadHaltException(url, error.reason.lower())


def unpack_with_promote(file, dest, remove_dst=True):
    """Unzip <file> into the directory <dest>.

    If all files in the zip file are under a top level directory,
    remove the top level dir and promote the dir level of those files.

    If <remove_dst> is True, then the directory <dest> will be remove first,
    otherwise, unextracted files will co-exist with those already in <dest>.

    Return whether promotion happend and the top level dir if did.
    """

    logger = logging.getLogger(__name__)

    # Check if need to remove <dest>.

    if remove_dst:
        remove_file_or_dir(dest)

    # Figure out if <file> is a Zipball or Tarball.

    if is_mlm_zip(file):
        opener, lister_name, appender_name = zipfile.ZipFile, 'namelist', 'write'
    else:
        opener, lister_name, appender_name = tarfile.open, 'getnames', 'add'

    # Unpack <file>.

    with opener(file) as pkg_file:

        # Check if all files are under a top dir.

        file_list = getattr(pkg_file, lister_name)()
        first_segs = [x.split(os.path.sep)[0] for x in file_list]
        if (len(file_list) == 1 and os.path.sep in file_list[0]) or \
                (len(file_list) != 1 and all([x == first_segs[0] for x in first_segs])):
            promote, top_dir = True, file_list[0].split(os.path.sep)[0]
        else:
            promote, top_dir = False, None

        if not promote:  # All files are at the top level.

            logger.debug("Extract {} directly into {}".format(file, dest))
            pkg_file.extractall(dest)
            return False, top_dir, file_list

        else:  # All files are under a top dir.
            logger.debug("Extract {} without top dir into {}".format(file, dest))
            file_list = []
            with tempfile.TemporaryDirectory() as tmpdir:

                # Extract file.

                pkg_file.extractall(tmpdir)

                with tempfile.TemporaryDirectory() as tmpdir2:

                    # Repack files without top dir and then extract again into <dest>.
                    #
                    # Extraction can be done on a existing dir, without removing the dir first,
                    # and the extracted files can co-exist with the files already inside the dir,
                    # without affecting the existing files except they have the same name.

                    with opener(os.path.join(tmpdir2, 'tmpball'), 'w') as new_pkg_file:
                        appender = getattr(new_pkg_file, appender_name)
                        dir_path = os.path.join(tmpdir, top_dir)
                        for path, dirs, files in os.walk(dir_path):
                            for file in files:
                                file_path = os.path.join(path, file)
                                arc_path = os.path.relpath(file_path, dir_path)
                                file_list.append(arc_path)
                                appender(file_path, arc_path)

                    with opener(os.path.join(tmpdir2, 'tmpball')) as new_pkg_file:
                        new_pkg_file.extractall(dest)

            return True, top_dir, file_list


def remove_file_or_dir(path):
    """Remove an existing file or directory."""

    if os.path.exists(path):
        if os.path.isfile(path):
            os.remove(path)
        else:
            shutil.rmtree(path)


def ends_with_mlm(name):
    """Check if name ends with .mlm or .aipk"""

    return name.endswith(EXT_MLM) or name.endswith(EXT_AIPK)


def is_url(name):
    """Check if name is a url."""

    return re.findall('http[s]?:', name)


def is_github_url(name):
    """Check if name starts with http://github.com or https://github.com"""

    return is_url(name) and name.lower().split('/')[2].endswith("github.com")


def is_mlm_zip(name):
    """Check if name is a MLM or Zip file."""

    return ends_with_mlm(name) or name.endswith(".zip")


def is_tar(name):
    """Check if name is a Tarball."""

    return name.endswith(".tar") or name.endswith(".gz") or name.endswith(".bz2")


def is_description_file(name):
    """Check if name ends with DESCRIPTION.yaml or DESCRIPTION.yml"""

    return name.endswith(DESC_YAML) or name.endswith(DESC_YML) or name.endswith(MLHUB_YAML)


def get_model_info_from_repo(model, mlhub):
    """Get model url on mlhub.

    Args:
        model (str): model name.
        mlhub (str): packages list url.

    Returns:
        url: model url for download.
        meta: list of all model meta data.

    Raises:
        ModelNotFoundOnRepoException
    """

    url = None
    version = None
    mlhub = get_repo(mlhub)
    meta = get_repo_meta_data(mlhub)
    
    # Find the first matching entry in the meta data.
    
    for entry in meta:
        if model == entry["meta"]["name"]:
            url = entry["meta"]["url"]
            if is_mlm_zip(url):
                version = entry["meta"]["version"]
            break
    
    # If not found suggest how a model might be installed.
    
    if url is None:
        logger = logging.getLogger(__name__)
        logger.error("Model '{}' not found on Repo '{}'.".format(model, mlhub))
        raise ModelNotFoundOnRepoException(model, mlhub)

    return url, version, meta


def dir_size(dirpath):
    """Get total size of dirpath."""

    return sum([sum(map(lambda f: os.path.getsize(os.path.join(pth, f)), files))
                for pth, dirs, files in os.walk(dirpath)])


def yes_or_no(msg, *params, yes=True):
    """Query yes or no with message.

    Args:
        msg (str): Message to be printed out.
        yes (bool): Indicates whether the default answer is yes or no.
    """

    print(msg.format(*params) + (' [Y/n]?' if yes else ' [y/N]?'), end=' ')
    choice = input().lower()

    answer = True if yes else False

    if yes and choice == 'n':
        answer = False

    if not yes and choice == 'y':
        answer = True

    return answer

# ----------------------------------------------------------------------
# Model package developer utilities
# ----------------------------------------------------------------------


def get_package_name():
    """Return the model pkg name.

    It is used by model pkg developer.
    """

    return os.environ.get('_MLHUB_MODEL_NAME', '')


def get_cmd_cwd():
    """Return the dir where model pkg command is invoked.

    For example, if `cd /temp; ml demo xxx`, then get_cmd_cwd() returns `/temp`.
    It is used by model pkg developer, and is different from where the model pkg script is located.

    `CMD_CWD` is a environment variable passed by mlhub.utils.dispatch() when invoke model pkg script.
    """

    return os.environ.get('_MLHUB_CMD_CWD', '')


def get_package_dir(model=None):
    """Return the dir where the model package should be installed."""

    return os.path.join(MLINIT, get_package_name() if model is None else model)


def create_package_dir(model=None):
    """Check existence of dir where the model package is installed, if not create it and return."""

    path = get_package_dir(model)

    return _create_dir(
        path,
        'Model package dir creation failed: {}'.format(path),
        ModelPkgDirCreateException(path)
    )


def get_package_cache_dir(model=None):
    """Return the dir where the model package stores cached files, such as pre-built model, data, image files, etc."""

    return os.path.join(CACHE_DIR, get_package_name() if model is None else model)


def create_package_cache_dir(model=None):
    """Check existence of dir where the model package stores cached files, If not create it and return."""

    path = get_package_cache_dir(model)

    return _create_dir(
        path,
        'Model package cache dir creation failed: {}'.format(path),
        ModelPkgCacheDirCreateException(path)
    )

# ----------------------------------------------------------------------
# Bash completion helper
# ----------------------------------------------------------------------


def create_completion_dir():
    """Check if the init dir exists and if not then create it."""

    return _create_dir(
        COMPLETION_DIR,
        'Bash completion dir creation failed: {}'.format(COMPLETION_DIR),
        CompletionDirCreateException(COMPLETION_DIR)
    )


def update_completion_list(completion_file, new_words):
    """Update specific completion list.
    Args:
        completion_file (str): full path of the completion file
        new_words (set): set of new words
    """

    logger = logging.getLogger(__name__)
    logger.info('Update bash completion cache.')
    logger.debug('Completion file: {}'.format(completion_file))
    logger.debug('New completion words: {}'.format(new_words))

    create_completion_dir()

    if os.path.exists(completion_file):
        with open(completion_file, 'r') as file:
            old_words = {line.strip() for line in file if line.strip()}
            logger.debug('Old Completion words: {}'.format(old_words))

        words = old_words | new_words
    else:
        words = new_words

    logger.debug('All completion words: {}'.format(words))
    with open(completion_file, 'w') as file:
        file.write('\n'.join(words))


def get_completion_list(completion_file):
    """Get the list of available words from cached completion file."""

    words = set()
    if os.path.exists(completion_file):
        with open(completion_file) as file:
            words = {line.strip() for line in file if line.strip()}

    print('\n'.join(words))

# -----------------------------------------------------------------------
# Command line argument parse helper
# -----------------------------------------------------------------------


class SubCmdAdder(object):
    """Add the subcommands described in <commands> into <subparsers> with
corresponding functions defined in <module>."""

    def __init__(self, subparsers, module, commands):
        """
        Args:
            subparsers (argparse.ArgumentParser): to which the subcommand is added.
            module: the module which defines the actual function for the subcommand.
            commands (dict): meta info for the subcommand.
        """
        self.subparsers = subparsers
        self.module = module
        self.commands = commands
        self.logger = logging.getLogger(__name__)

    def add_subcmd(self, subcommand):
        """Add <subcommand> to subparsers."""

        cmd_meta = self.commands[subcommand]
        self.logger.debug("Add command line positioanl argument: {} - {}".format(subcommand, cmd_meta))

        parser = self.subparsers.add_parser(
            subcommand,
            aliases=cmd_meta.get('alias', ()),
            description=cmd_meta['description'],
        )

        if 'argument' in cmd_meta:
            args = cmd_meta['argument']
            for name in args:
                parser.add_argument(name, **args[name])

        if 'func' in cmd_meta:
            parser.set_defaults(func=getattr(self.module, cmd_meta['func']))

    def add_allsubcmds(self):
        """Add all subcommands described in <self.commands> into <self.subparsers>."""

        for cmd in self.commands:
            self.add_subcmd(cmd)


class OptionAdder(object):
    """Add the global options described in <options> into <parser>."""

    def __init__(self, parser, options):
        self.parser = parser
        self.options = options
        self.logger = logging.getLogger(__name__)

    def add_option(self, option):
        opt = self.options[option]
        opt_alias = [option, ]
        if 'alias' in opt:
            opt_alias += opt['alias']
            del opt['alias']
        self.logger.debug("Add command line optional argument: {} - {}".format(opt_alias, opt))
        self.parser.add_argument(*opt_alias, **opt)

    def add_alloptions(self):
        for opt in self.options:
            self.add_option(opt)

# ----------------------------------------------------------------------
# Debug Log and Error Printing
# ----------------------------------------------------------------------


def create_log_dir():
    """Check if the log dir exists and if not then create it."""

    return _create_dir(
        LOG_DIR,
        'Log dir creation failed: {}'.format(LOG_DIR),
        LogDirCreateException(LOG_DIR)
    )


def add_log_handler(logger, handler, level, fmt):
    """Add handler with level and format to logger"""

    handler.setLevel(level)
    formatter = logging.Formatter(fmt)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def print_on_stderr(msg, *param):
    """Print msg on stderr"""

    print(msg.format(*param), file=sys.stderr)


def print_on_stderr_exit(msg, *param, exitcode=1):
    """Print msg on stderr and exit."""

    print_on_stderr(msg, *param)
    sys.exit(exitcode)


def print_error(msg, *param):
    """Print error msg with APPX prefix on stderr."""

    print_on_stderr(APPX + msg.format(*param))


def print_error_exit(msg, *param, exitcode=1):
    """Print error msg with APPX prefix on stderr and exit."""

    print_error(msg, *param)
    sys.exit(exitcode)

# ----------------------------------------------------------------------
# Custom Exceptions
# ----------------------------------------------------------------------


class ModelURLAccessException(Exception):
    pass


class ModelNotFoundOnRepoException(Exception):
    pass


class MalformedMLMFileNameException(Exception):
    pass


class RepoAccessException(Exception):
    pass


class MLInitCreateException(Exception):
    pass


class CompletionDirCreateException(Exception):
    pass


class DescriptionYAMLNotFoundException(Exception):
    pass


class ModelDownloadHaltException(Exception):
    pass


class ModelNotInstalledException(Exception):
    pass


class ModelReadmeNotFoundException(Exception):
    pass


class UnsupportedScriptExtensionException(Exception):
    pass


class CommandNotFoundException(Exception):
    pass


class LogDirCreateException(Exception):
    pass


class ModelPkgDirCreateException(Exception):
    pass


class ModelPkgCacheDirCreateException(Exception):
    pass


class LackDependencyException(Exception):
    pass


class ConfigureFailedException(Exception):
    pass


class DataResourceNotFoundException(Exception):
    pass


class MLTmpDirCreateException(Exception):
    pass


class MalformedYAMLException(Exception):
    pass


class YAMLFileAccessException(Exception):
    pass
