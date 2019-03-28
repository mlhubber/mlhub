#! /bin/bash -
# ----------------------------------------------------------------------
# This script is used for installing system packages required by model
# package.
# ----------------------------------------------------------------------

source $(dirname $0)/utils.sh

installedpkgs=
pkgstoinstall=

########################################################################
# Check packages already installed.
########################################################################

for pkg in $@; do
  if _is_system_pkg_installed ${pkg}; then
    installedpkgs+=" ${pkg}"
  else
    pkgstoinstall+=" ${pkg}"
  fi
done

if [[ ! -z ${installedpkgs} ]]; then
  echo
  echo '*** The following required system packages are already installed:'
  echo " ${installedpkgs}"
fi

########################################################################
# Install packages not installed.
# TODO: Do not install recommended system packages.
########################################################################

if [[ ! -z ${pkgstoinstall} ]]; then
  echo
  echo '*** Installing the following system dependencies:'
  echo " ${pkgstoinstall}"

  # sudo apt-get install -y wajig > /dev/null
  # wajig update > /dev/null
  # wajig distupgrade -y > /dev/null

  for pkg in ${pkgstoinstall}; do
    msg="\nDo you want to install ${pkg}"
    if [[ ! -z ${_MLHUB_OPTION_YES} ]] || _is_yes "${msg}"; then
      sudo apt-get install -y ${pkg}

    # Or:
    # wajig install -y ${pkg}

      _check_returncode

    fi
  done
fi
