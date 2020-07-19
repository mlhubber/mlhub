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

import distro
import glob
import json
import logging
import mlhub.utils as utils
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import urllib.request
import yaml

from distutils.version import StrictVersion
from mlhub.constants import (
    BASH_CMD,
    EXT_MLM,
    MLHUB_YAML,
    README,
)

# The commands are implemented here in a logical order with each
# command providing a suggesting of the following command.


# ------------------------------------------------------------------------
# AVAILABLE
# ------------------------------------------------------------------------


def list_available(args):
    """List the name and title of the models in the Hub."""

    # Setup.

    logger = logging.getLogger(__name__)
    logger.info("List available models.")
    logger.debug(f"args: {args}")

    meta, repo = utils.get_repo_meta_data(args.mlhub)
    model_names = [entry["meta"]["name"] for entry in meta]

    # Update bash completion list.

    utils.update_model_completion(set(model_names))

    # List model name only.

    if args.name_only:
        print("\n".join(model_names))
        return

    # Provide some context.

    if not args.quiet:
        msg = "The repository '{}' provides the following models:\n"
        print(msg.format(repo))

    # List the meta data.

    for entry in meta:
        utils.print_meta_line(entry)

    # Suggest next step.

    if not args.quiet:
        utils.print_next_step("available")
        if not os.path.exists(utils.get_init_dir()):
            print(
                "Why not give the 'rain' model a go...\n\n"
                "  $ ml install rain\n"
            )


# ------------------------------------------------------------------------
# INSTALLED
# ------------------------------------------------------------------------


def list_installed(args):
    """List the installed models."""

    logger = logging.getLogger(__name__)
    logger.info("List installed models.")

    # Find installed models, ignoring special folders like R.

    init = utils.get_init_dir()
    if os.path.exists(init):
        msg = f" in '{init}'."
        models = [
            f
            for f in os.listdir(init)
            if os.path.isdir(os.path.join(init, f))
            and f != "R"
            and not f.startswith(".")
            and not f.startswith("_")
        ]
    else:
        msg = f". '{init}' does not exist."
        models = []

    models.sort()

    # Only list model names

    if args.name_only:
        print("\n".join(models))
        return

    # Report on how many models we found installed.

    mcnt = len(models)
    plural = "s" if mcnt != 1 else ""
    print(f"Found {mcnt} model{plural} installed{msg}")

    # Report on each of the installed models.

    if mcnt > 0:
        print("")

    invalid_models = []
    for p in models:
        try:
            entry = utils.load_description(p)
            utils.print_meta_line(entry)
        except (
            utils.DescriptionYAMLNotFoundException,
            utils.MalformedYAMLException,
            KeyError,
        ):
            mcnt -= 1
            invalid_models.append(p)
            continue

        # Update bash completion list.

        if "commands" in entry:
            utils.update_command_completion(set(entry["commands"]))

    invalid_mcnt = len(invalid_models)
    if invalid_mcnt > 0:
        print(
            "\nOf which {} model package{} {} broken:\n".format(
                invalid_mcnt,
                "s" if invalid_mcnt > 1 else "",
                "are" if invalid_mcnt > 1 else "is",
            )
        )
        print("  ====> \033[31m" + ", ".join(invalid_models) + "\033[0m")
        print(utils.get_command_suggestion("remove"))

    # Suggest next step.

    if not args.quiet:
        if mcnt > 0:
            utils.print_next_step("installed", scenario="exist")
        else:
            utils.print_next_step("installed", scenario="none")


# -----------------------------------------------------------------------
# INSTALL
# ------------------------------------------------------------------------


def install_model(args):
    """Install a model.

    Args:
        args: Command line args parsed by argparse.
        args.model (str): mlm/zip path, mlm/zip url, model name, GitHub repo,
                          like mlhubber/mlhub, or MLHUB.yaml on github repo,
                          like mlhubber/audit:doc/MLHUB.yaml.
    """

    logger = logging.getLogger(__name__)
    logger.info("Install a model.")
    logger.debug(f"args: {args}")

    # Avoid 403 errors which result when the header identifies itself
    # as python urllib or is empty and thus the web site assumes it is
    # a robot. We are not a robot but a user downloading a file. This
    # will ensure gitlab is oaky with retrieving from a URL by adding
    # a header rather than no header. TODO move to using Requests.
    
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)

    model = args.model  # model pkg name
    location = args.model  # pkg file path or URL
    key = args.i  # SSH key
    version = None  # model pkg version
    mlhubyaml = None  # MLHUB.yaml path or URL
    repo_obj = None  # RepoTypeURL object for related URL interpretation
    maybe_private = False  # Maybe private repo

    # Obtain the model URL if not a local file.

    if (
        not utils.is_archive_file(model)
        and not utils.is_url(model)
        and "/" not in model
    ):

        # Model package name, which can be found in mlhub repo.
        # Like:
        #     $ ml install audit
        #
        # We assume the URL got from mlhub repo is a link to a mlm/zip/tar file
        # or a GitHub repo reference or MLHUB.yaml.

        # Correct model name if possible.

        matched_model = utils.get_misspelled_pkg(model)
        if matched_model is not None:
            model = matched_model

        # Get model pkg meta data from mlhub repo.

        location, version, meta_list = utils.get_model_info_from_repo(
            model, args.mlhub
        )

        # Update bash completion list.

        utils.update_model_completion({e["meta"]["name"] for e in meta_list})

    if not utils.is_archive_file(location):

        # Model from a repo such as GitHub, GitLab, Bitbucket etc.
        #
        # Possible options are:
        #   $ ml install mlhubber/audit            # latest commit on the master branch of GitHub repo mlhubber/audit
        #   $ ml install mlhubber/audit@dev        # latest commit on the dev branch of GitHub repo mlhubber/audit
        #   $ ml install mlhubber/audit@0001ea4    # commit 0001ea4 of mlhubber/audit
        #   $ ml install mlhubber/audit:doc/MLHUB.yaml            # latest commit on master, but a specified YAML file
        #   $ ml install https://github.com/mlhubber/audit/...    # Arbitrary GitHub link address
        #
        #   $ ml install github:mlhubber/audit    # GitHub repo, the same as ml install mlhubber/audit
        #
        #   $ ml install gitlab:mlhubber/audit@2fe89kh:doc/MLHUB.yaml    # GitLab repo
        #   $ ml install https://https://gitlab.com/mlhubber/audit/...   # GitLab repo
        #
        #   $ ml install bitbucket:mlhubber/audit                        # BitBucket repo
        #   $ ml install https://bitbucket.org/mlhubber/audit/...        # BitBucket repo

        repo_obj = utils.RepoTypeURL.get_repo_obj(location)
        try:
            mlhubyaml = repo_obj.get_pkg_yaml_url()
            location = repo_obj.compose_repo_zip_url()
            logger.debug(f"location: {location}")
            logger.debug(f"mlhubyaml: {mlhubyaml}")
        except utils.DescriptionYAMLNotFoundException:  # Maybe private repo
            maybe_private = True
            pass

    # Determine the path of downloaded/existing model package file

    pkgfile = None
    if maybe_private:  # Maybe private repo
        pkgfile = repo_obj.repo
    elif utils.is_archive_file(location):
        pkgfile = os.path.basename(location)  # pkg file name
    elif utils.is_url(location):
        pkgfile = utils.get_url_filename(location)

    # Query archive type if not available from file name per se.

    if not maybe_private:
        while pkgfile is None or not utils.is_archive_file(pkgfile):
            print(
                "The file type cannot be determined.\n"
                "Please give it a file name with explicit valid archive extension: ",
                end="",
            )
            pkgfile = input()

    if maybe_private:
        uncompressdir = pkgfile
    else:
        uncompressdir = pkgfile[
            : pkgfile.rfind(".")
        ]  # Dir Where pkg file is extracted

    # Installation.

    entry = None  # Meta info read from MLHUB.yaml
    with tempfile.TemporaryDirectory() as mlhubtmpdir:

        # Determine the local path of the model package

        if maybe_private:
            local = None
        elif utils.is_url(location):
            local = os.path.join(mlhubtmpdir, pkgfile)  # downloaded
        else:
            local = location  # local file path

        uncompressdir = os.path.join(mlhubtmpdir, uncompressdir)

        # Obtain model version.

        if version is None:
            if utils.ends_with_mlm(
                pkgfile
            ):  # Get version number from MLM file name.

                model, version = utils.interpret_mlm_name(pkgfile)

            elif not repo_obj:

                # Get MLHUB.yaml inside the archive file.

                if utils.is_url(
                    location
                ):  # Download the package file because it is not from GitHub.
                    utils.download_model_pkg(
                        location, local, pkgfile, args.quiet
                    )

                if not args.quiet:
                    print("Extracting '{}' ...\n".format(pkgfile))

                utils.unpack_with_promote(
                    local, uncompressdir, valid_name=pkgfile
                )
                mlhubyaml = utils.get_available_pkgyaml(
                    uncompressdir
                )  # Path to MLHUB.yaml

            elif maybe_private:

                identity_env = (
                    "GIT_SSH_COMMAND='ssh -i {}' ".format(key) if key else ""
                )
                command = "cd {}; {}git clone {}; cd {}; git checkout {}".format(
                    mlhubtmpdir,
                    identity_env,
                    repo_obj.get_ssh_clone_url(),
                    repo_obj.repo,
                    repo_obj.ref,
                )
                proc = subprocess.Popen(
                    command, shell=True, stderr=subprocess.PIPE
                )
                output, errors = proc.communicate()
                if proc.returncode != 0:
                    raise utils.InstallFailedException(errors.decode("utf-8"))

                if repo_obj.path:
                    mlhubyaml = os.path.join(uncompressdir, repo_obj.path)
                else:
                    mlhubyaml = utils.get_available_pkgyaml(
                        uncompressdir
                    )  # Path to MLHUB.yaml

            if mlhubyaml is not None:  # Get version number from MLHUB.yaml
                entry = utils.read_mlhubyaml(mlhubyaml)
                meta = entry["meta"]
                model = meta["name"]
                version = meta["version"]

            utils.update_model_completion(
                {model}
            )  # Update bash completion list.

        # Check if model is already installed.

        install_path = utils.get_package_dir(model)  # Installation path
        if os.path.exists(install_path):
            installed_version = utils.load_description(model)["meta"][
                "version"
            ]

            # Ensure version number is string.

            installed_version = str(installed_version)
            version = str(version)

            if StrictVersion(installed_version) > StrictVersion(version):
                yes = utils.yes_or_no(
                    "Downgrade '{}' from version '{}' to version '{}'",
                    model,
                    installed_version,
                    version,
                    yes=True,
                )
            elif StrictVersion(installed_version) == StrictVersion(version):
                yes = utils.yes_or_no(
                    "Replace '{}' version '{}' with version '{}'",
                    model,
                    installed_version,
                    version,
                    yes=True,
                )
            else:
                yes = utils.yes_or_no(
                    "Upgrade '{}' from version '{}' to version '{}'",
                    model,
                    installed_version,
                    version,
                    yes=True,
                )

            if not yes:
                # Suggest next step before exiting, as if an install has just happened.
                utils.print_next_step("install", model=model)
                sys.exit(0)
            else:
                print()

            shutil.rmtree(install_path)

        # Uncompress package file.

        if not os.path.exists(
            uncompressdir
        ):  # Model pkg mlm or GitHub pkg has not unzipped yet.
            if utils.is_url(location):  # Download the package file if needed.
                utils.download_model_pkg(location, local, pkgfile, args.quiet)

            if not args.quiet:
                print("Extracting '{}' ...\n".format(pkgfile))

            utils.unpack_with_promote(local, uncompressdir, valid_name=pkgfile)

        # Install package files.
        #
        # Because it is time-consuming to download all package files one-by-one , we
        # download the whole zipball from the repo first, then re-arrange the files
        # according to `dependencies` -> `files` in MLHUB.yaml if any.

        # Find if any files specified in MLHUB.yaml

        if (
            mlhubyaml is None
        ):  # MLM file which can obtain version number from it name.
            mlhubyaml = utils.get_available_pkgyaml(uncompressdir)
            entry = utils.read_mlhubyaml(mlhubyaml)

        depspec = None
        if "dependencies" in entry:
            depspec = entry["dependencies"]
        elif "dependencies" in entry["meta"]:
            depspec = entry["meta"]["dependencies"]

        file_spec = None
        if depspec is not None and "files" in depspec:
            file_spec = {"files": depspec["files"]}
        elif "files" in entry:
            file_spec = {"files": entry["files"]}

        if (
            file_spec is not None
        ):  # install package files if they are specified in MLHUB.yaml

            # MLHUB.yaml should always be at the package root.

            os.mkdir(install_path)
            if utils.is_url(
                mlhubyaml
            ):  # We currently only support MLHUB.yaml specified on GitHub.
                if mlhubyaml.startswith("https://api"):
                    urllib.request.urlretrieve(
                        json.loads(urllib.request.urlopen(mlhubyaml).read())[
                            "download_url"
                        ],
                        os.path.join(install_path, MLHUB_YAML),
                    )
                else:
                    urllib.request.urlretrieve(
                        mlhubyaml, os.path.join(install_path, MLHUB_YAML)
                    )
            else:
                shutil.move(mlhubyaml, install_path)

            # All package files except MLHUB.yaml should be specified in 'files' of MLHUB.yaml

            try:
                utils.install_file_deps(
                    utils.flatten_mlhubyaml_deps(file_spec)[0][1],
                    model,
                    downloadir=uncompressdir,
                    yes=True,
                )
            except utils.ModelPkgInstallationFileNotFoundException:
                if os.path.exists(install_path):
                    shutil.rmtree(install_path)

                raise

        else:
            # Otherwise, put all files under package dir.
            # **Note** Here we must make sure <install_path> does not exist.
            # Otherwise, <unzipdir> will be inside <install_path>
            shutil.move(uncompressdir, install_path)

        # Update bash completion list.

        utils.update_command_completion(
            set(utils.load_description(model)["commands"])
        )

        # Update working dir if any.

        if args.working_dir is not None:
            utils.update_working_dir(model, args.working_dir)

        if not args.quiet:

            # Informative message about the size of the installed model.

            msg  = f"Found '{model}' version {version}.\n\nInstalled '{model}' "
            msg += f"into '{install_path}/' ({utils.dir_size(install_path):,} bytes)."
            print(msg)

            # Suggest next step. README or DOWNLOAD

            utils.print_next_step("install", model=model)


# -----------------------------------------------------------------------
# DOWNLOAD
# ------------------------------------------------------------------------


def download_model(args):
    """Download the large pre-built model."""

    # TODO: Will this be a url in the DESCRIPTION file or will it be a
    # download.sh script. Which ever (maybe either), if it is present
    # then this command is available and will download the required
    # file, perhaps from the actual source of the model.

    model = args.model

    # Check that the model is installed.

    utils.check_model_installed(model)

    if not args.quiet:
        utils.print_next_step("download", model=model)


# ------------------------------------------------------------------------
# README
# ------------------------------------------------------------------------


def readme(args):
    """Display the model's README information."""

    model = args.model

    # Correct model name if possible.

    matched_model = utils.get_misspelled_pkg(model)
    if matched_model is not None:
        model = matched_model

    # Setup.

    logger = logging.getLogger(__name__)
    logger.info("Get README of {}.".format(model))

    path = utils.get_package_dir(model)
    readme_file = os.path.join(path, README)

    # Check that the model is installed.

    utils.check_model_installed(model)

    # Display the README.

    if not os.path.exists(
        readme_file
    ):  # Try to generate README from README.md
        readme_raw = readme_file[: readme_file.rfind(".")] + ".md"
        if not os.path.exists(readme_raw):
            readme_raw = readme_raw[: readme_raw.rfind(".")] + ".rst"
            if not os.path.exists(readme_raw):
                raise utils.ModelReadmeNotFoundException(model, readme_file)

        script = os.path.join(
            os.path.dirname(__file__), "scripts", "convert_readme.sh"
        )
        command = "{} {} {} {}".format(BASH_CMD, script, readme_raw, README)
        proc = subprocess.Popen(
            command, shell=True, cwd=path, stderr=subprocess.PIPE
        )
        output, errors = proc.communicate()
        if proc.returncode != 0:
            errors = errors.decode("utf-8")
            command_not_found = re.compile(r"\d: (.*):.*not found").search(
                errors
            )
            if command_not_found is not None:
                raise utils.LackPrerequisiteException(
                    command_not_found.group(1)
                )

            print("An error was encountered:\n")
            print(errors)
            raise utils.ModelReadmeNotFoundException(model, readme_file)

    with open(readme_file, "r") as f:
        print(utils.drop_newline(f.read()))

    # Suggest next step.

    if not args.quiet:
        utils.print_next_step("readme", model=model)


# ------------------------------------------------------------------------
# LICENSE
# ------------------------------------------------------------------------


def license(args):
    """Display the mode's LICENSE information."""

    print("Please assist by implementing this command.")


# -----------------------------------------------------------------------
# COMMANDS
# ------------------------------------------------------------------------


def list_model_commands(args):
    """ List the commands supported by this model."""

    model = args.model

    # Correct model name if possible.

    matched_model = utils.get_misspelled_pkg(model)
    if matched_model is not None:
        model = matched_model

    logger = logging.getLogger(__name__)
    logger.info("List available commands of '{}'".format(model))

    # Check that the model is installed.

    utils.check_model_installed(model)

    entry = utils.load_description(model)
    commands = entry["commands"]

    if args.name_only:
        print("\n".join(list(commands)))
        return

    msg = "The '{}' model "
    meta = entry["meta"]
    if "title" not in meta:
        title = None
    else:
        title = utils.lower_first_letter(utils.dropdot(meta["title"]))
        msg += "({}) "

    msg += "supports the following commands:"
    msg = msg.format(model, title)
    msg = textwrap.fill(msg, width=75)
    print(msg)

    for cmd in commands:
        utils.print_model_cmd_help(entry, cmd)

    # Update bash completion list.

    utils.update_command_completion(set(commands))

    # Suggest next step.

    if not args.quiet:
        utils.print_next_step("commands", description=entry, model=model)


# -----------------------------------------------------------------------
# CONFIGURE
# ------------------------------------------------------------------------


def configure_model(args):
    """Ensure the user's environment is configured."""

    # TODO: Add support for additional configuration if any except those
    #       specified in MLHUB.yaml.
    # TODO: When fail, print out the failed dep, as well as installed
    #       deps and non-installed deps.
    # TODO: Add support for specifying packages version.
    # TODO: Add more informative messages for different kinds of
    #       dependencies.

    # Other ideas for configuration
    #
    # 1 Construct mlhub container (from Ubuntu) with known starting point
    #
    # 2 Assume the user is on a DSVM with free Azure account to test out.
    #
    # 3 Read dependencies: and language: and then install as required:
    #
    # 4 Assume model packager provides a configure.R script. This is a
    #   override and no other configuration happens if this is
    #   supplied. Alternatively this is viewed as a cop-out providing
    #   no support from mlhub for the model packager. The preference
    #   would be to use the dependencies: tag to list the required R
    #   or python packages.
    #
    # So the meta-code might be
    #
    #   if file.exists(configure.XX):
    #     XX configure.XX
    #   else if language: == "Rscript":
    #     packages <- dependencies:
    #     install  <- packages[!(packages %in% installed.packages()[,"Package"])]
    #     if(length(new.packages)) install.packages(install)
    #   else if language: == "python":
    #     packages = dependencies:
    #     cat packages > requirements.txt
    #     pip install -r requirements.txt
    #

    YES = args.y | args.yes

    # Avoid 403 errors which result when the header identifies itself
    # as python urllib or is empty and thus the web site assumes it is
    # a robot. We are not a robot but a user downloading a file. This
    # will ensure gitlab is oaky with retrieving from a URL by adding
    # a header rather than no header. TODO move to using Requests.
    
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)

    if not args.model:

        # Configure MLHUB per se.
        # Includes bash completion and system pre-requisites

        if distro.id() in ["debian", "ubuntu"]:
            path = os.path.dirname(__file__)
            env_var = "export _MLHUB_OPTION_YES='y'; " if YES else ""
            env_var += 'export _MLHUB_PYTHON_EXE="{}"; '.format(sys.executable)
            script = os.path.join("scripts", "dep", "mlhub.sh")
            command = "{}{} {}".format(env_var, BASH_CMD, script)
            proc = subprocess.Popen(
                command, shell=True, cwd=path, stderr=subprocess.PIPE
            )
            output, errors = proc.communicate()
            if proc.returncode != 0:
                raise utils.ConfigureFailedException(errors.decode("utf-8"))

        return

    # Model package configuration.

    model = args.model

    # Correct model name if possible.

    matched_model = utils.get_misspelled_pkg(model)
    if matched_model is not None:
        model = matched_model

    # Setup.

    pkg_dir = utils.get_package_dir(model)

    # Check if the model package is installed.

    utils.check_model_installed(model)

    # Install dependencies specified in MLHUB.yaml

    entry = utils.load_description(model)
    depspec = None
    if "dependencies" in entry:
        depspec = entry["dependencies"]
    elif "dependencies" in entry["meta"]:
        depspec = entry["meta"]["dependencies"]

    if depspec is not None:
        for spec in utils.flatten_mlhubyaml_deps(depspec):
            category = spec[0][-1]
            deplist = spec[1]

            # Category include:
            #   ------------------------------------------------------------------------------
            #           category | action
            #   -----------------|------------------------------------------------------------
            #              None  |  install package according to entry['meta']['languages']
            #                    |  if R,      install.packages(xxx) from cran;
            #                    |  if Python, pip install xxx
            #   -----------------|------------------------------------------------------------
            #            system  |  apt-get install
            #                sh  |  apt-get install
            #   -----------------|------------------------------------------------------------
            #                 r  |  install.packages(xxx) from cran, version can be specified
            #              cran  |  install.packages(xxx) from cran, version can be specified
            #   cran-2018-12-01  |  install cran snapshot on 2018-12-01
            #            github  |  devtools::install_github from github
            #   -----------------|------------------------------------------------------------
            #            python  |  apt-get install python-xxx
            #           python3  |  apt-get install python3-xxx
            #               pip  |  pip install
            #              pip3  |  pip3 install
            #             conda  |  conda install
            #   -----------------|------------------------------------------------------------
            #             files  |  download files
            #   -----------------|------------------------------------------------------------

            # ----- Determine deps by language -----

            if category is None:

                lang = entry["meta"]["languages"].lower()
                if lang == "r":
                    utils.install_r_deps(
                        deplist, model, source="cran", yes=YES
                    )
                elif "python".startswith(lang):
                    utils.install_python_deps(
                        deplist, model, source="pip", yes=YES
                    )

            # ----- System deps -----

            elif category == "system" or "shell".startswith(category):
                utils.install_system_deps(deplist, yes=YES)

            # ----- R deps -----

            elif category == "r":
                utils.install_r_deps(deplist, model, source="cran", yes=YES)

            elif (
                category == "cran"
                or category == "github"
                or category.startswith("cran-")
            ):
                utils.install_r_deps(deplist, model, source=category, yes=YES)

            # ----- Python deps -----

            elif (
                category.startswith("python")
                or category.startswith("pip")
                or category == "conda"
            ):
                utils.install_python_deps(
                    deplist, model, source=category, yes=YES
                )

            # ----- Files -----

            elif "files".startswith(category):
                utils.install_file_deps(deplist, model, key=args.i, yes=YES)

    # Run additional configure script if any.

    conf = utils.configure(pkg_dir, "configure.sh", args.quiet) or True
    conf = utils.configure(pkg_dir, "configure.R", args.quiet) or conf
    conf = utils.configure(pkg_dir, "configure.py", args.quiet) or conf

    if not conf:
        if depspec is not None:
            msg = (
                "No configuration script provided for this model. "
                "The following dependencies are required:\n"
            )
            print(msg)
            print(yaml.dump(depspec))
        else:
            print("No configuration provided (maybe none is required).")

    # Update working dir if any.

    if args.working_dir is not None:
        utils.update_working_dir(model, args.working_dir)

    # Suggest next step.

    if not args.quiet:
        utils.print_next_step("configure", model=model)


# -----------------------------------------------------------------------
# DISPATCH
# ------------------------------------------------------------------------


def dispatch(args):
    """Dispatch other commands to the appropriate model provided script."""

    cmd = args.cmd
    model = args.model
    path = utils.get_package_dir(model)

    param = " ".join(args.param)

    # Get working dir if any.

    if args.working_dir is not None:
        utils.update_working_dir(model, args.working_dir)
        if args.working_dir == "":
            args.working_dir = None
    else:
        args.working_dir = utils.get_working_dir(model)

    # Get conda environment name if any.

    conda_env_name = utils.get_conda_env_name(model)

    # Check that the model is installed and has commands.

    utils.check_model_installed(model)

    entry = utils.load_description(model)

    if "commands" not in entry or len(entry["commands"]) == 0:
        raise utils.CommandNotFoundException(cmd, model)

    # Correct misspelled command if possible.

    matched_cmd = utils.get_misspelled_command(cmd, list(entry["commands"]))
    if matched_cmd is not None:
        cmd = matched_cmd

    # Check if cmd needs to use graphic display indicated in DESCRIPTION.yaml.

    meta = entry["meta"]
    if (
        "display" in meta
        and cmd in meta["display"]
        and os.environ.get("DISPLAY", "") == ""
    ):
        msg = "Graphic display is required but not available for command '{}'. Continue"
        yes = utils.yes_or_no(msg, cmd, yes=False)
        if not yes:
            msg = """
To enable DISPLAY be sure to connect to the server using 'ssh -X'
or else connect to the server's desktop using a local X server like X2Go.

"""
            sys.stdout.write(msg)
            sys.exit(1)

    # Obtain the default/chosen language for the package.

    lang = meta["languages"]

    # Deal with malformed 'languages' field

    lang_opts = {"python": "py", "R": "R"}
    for k in list(lang_opts):
        if lang in k:
            lang = lang_opts[k]
            break

    # Obtain the specified script file.

    script = cmd + "." + lang

    logger = logging.getLogger(__name__)
    logger.debug("Execute the script: " + os.path.join(path, script))

    if cmd not in list(entry["commands"]) or not os.path.exists(
        os.path.join(path, script)
    ):
        raise utils.CommandNotFoundException(cmd, model)

    # Determine the interpreter to use
    #
    # .R => Rscript; .py => python, etc.

    interpreter = utils.interpreter(script)

    # Change working dir if needed

    if args.working_dir is not None:
        script = os.path.join(path, script)
        path = args.working_dir

    # _MLHUB_CMD_CWD: a environment variable indicates current working
    #                 directory where command `ml xxx` is invoked.
    # _MLHUB_MODEL_NAME: env variable indicates the name of the model.
    #
    # The above two env vars can be obtained by helper function, such
    # as utils.get_cmd_cwd().  And model package developer should be
    # use the helper function instead of the env vars directly.

    env_var = "export _MLHUB_CMD_CWD='{}'; ".format(os.getcwd())
    env_var += "export _MLHUB_MODEL_NAME='{}'; ".format(model)
    env_var += (
        'export _MLHUB_PYTHON_EXE="{}"; '.format(sys.executable)
        if not conda_env_name
        else ""
    )
    if not conda_env_name and script.endswith(
        "py"
    ):  # Handle python environment
        env_var += utils.get_py_pkg_path_env(model)

    command = "{}{} {} {}".format(
        env_var, interpreter if not conda_env_name else "python", script, param
    )

    # Run script inside conda environment if specified

    if conda_env_name is not None:
        command = '{} -ic "conda activate {}; {}"'.format(
            BASH_CMD, conda_env_name, command
        )

    logger.debug("(cd " + path + "; " + command + ")")

    proc = subprocess.Popen(command, shell=True, cwd=path)
    output, errors = proc.communicate()
    missing_r_dep = False
    if proc.returncode != 0 and errors:
        errors = errors.decode("utf-8")

        # Check if it is Python dependency unsatisfied

        dep_required = re.compile(
            r"ModuleNotFoundError: No module named '(.*)'"
        ).search(errors)

        # Check if R dependency unsatisfied

        if dep_required is None:
            dep_required = re.compile(
                r"there is no package called ‘(.*)’"
            ).search(errors)
            if dep_required is not None:
                missing_r_dep = True

        # Check if required data resource not found

        data_required = re.compile(
            r"mlhub.utils.DataResourceNotFoundException"
        ).search(errors)

        if dep_required is not None:  # Dependency unsatisfied
            dep_required = dep_required.group(1)
            logger.error(
                "Dependency unsatisfied: {}\n{}".format(dep_required, errors)
            )
            raise utils.LackDependencyException(
                dep_required, missing_r_dep, model
            )
        elif data_required is not None:  # Data not found
            raise utils.DataResourceNotFoundException()
        else:  # Other unknown errors
            print("An error was encountered:\n")
            print(errors)

    else:
        # Suggest next step - in the context of the command line view
        # of the tool, let's not provide a next step for now. 20190528

        if False:  # not args.quiet:
            utils.print_next_step(cmd, description=entry, model=model)


# ------------------------------------------------------------------------
# DONATE
# ------------------------------------------------------------------------


def donate(args):
    """Consider a donation to the author."""

    print(
        "Please assist by implementing this command: support donations to the author."
    )


# ------------------------------------------------------------------------
# CLEAN
# ------------------------------------------------------------------------


def remove_mlm(args):
    f"""Remove downloaded {EXT_MLM} files."""

    mlm = glob.glob(os.path.join(utils.get_init_dir(), "*.mlm"))
    mlm.sort()
    for m in mlm:
        if utils.yes_or_no("Remove model package archive '{}'", m, yes=True):
            os.remove(m)


# ------------------------------------------------------------------------
# REMOVE
# ------------------------------------------------------------------------


def remove_model(args):
    """Remove installed model."""

    # TODO: Remove .archive and .config for the model.

    model = args.model

    # Determine if remove all model pkgs or a certain model pkg.

    cache = None
    if model is None:
        path = utils.get_init_dir()
        if os.path.exists(path):
            msg = "*Completely* remove all installed models in '{}'"
        else:
            msg = "The local model folder '{}' does not exist. Nothing to do."
            msg = msg.format(path)
            print(msg)
            return
    else:

        # Correct model name if possible.

        matched_model = utils.get_misspelled_pkg(model)
        if matched_model is not None:
            model = matched_model

        path = utils.get_package_dir(model)
        if os.path.exists(utils.get_package_cache_dir(model)):
            cache = utils.get_package_cache_dir(model)
        msg = "Remove '{}/'"

        # Check that the model is installed.

        utils.check_model_installed(model)

    if utils.yes_or_no(msg, path, yes=True):

        # Remove package installation dir

        shutil.rmtree(path)

        # Remove package config dir as well without ask

        path = utils.get_package_config_dir(model)
        if os.path.exists(path):
            shutil.rmtree(path)

        # Ask if remove cached files

        if cache is not None and utils.yes_or_no(
            "Remove cache '{}/' as well", cache, yes=False
        ):
            shutil.rmtree(cache)
            archive = utils.get_package_archive_dir(model)
            if os.path.exists(archive):
                shutil.rmtree(archive)
    else:
        if model is None and not args.quiet:
            utils.print_next_step("remove")
