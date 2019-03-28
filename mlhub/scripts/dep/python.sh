#! /bin/bash -
# ----------------------------------------------------------------------
# This script is used for installing Python packages required by model
# package.
# ----------------------------------------------------------------------

source $(dirname $0)/utils.sh

# Python packages will be installed into package_path

package_path=$1
shift

# src indicates the type of Python packages: system, pip, conda, etc

src=$1
abbr=${src:0:3}
shift

if [[ ${abbr} == 'pyt' ]]; then  # Install Python package from system

  if [[ -n "$@" ]]; then
    pkgs=$(echo "$@" | sed 's/[^ ]* */'"${src}"'-&/g')
    ${bash} $(dirname $0)/system.sh ${pkgs}
    _check_returncode
  fi

elif [[ ${abbr} == 'pip' ]]; then  # pip install package

  # Check if the packages are already installed

  for pkg in "$@"; do

    name=${pkg%%[>=<]*}
    installed_version="$(_get_pip_pkg_version ${name})"
    if _is_version_satisfied "${pkg}" "${installed_version}"; then
      installedpkgs+=" ${pkg}"
    else
      pkgstoinstall+=" ${pkg}"
    fi

  done

  if [[ ! -z ${installedpkgs} ]]; then
    echo -e "\n*** The following required pip packages are already installed:"
    echo " ${installedpkgs}"
  fi

  for pkg in ${pkgstoinstall}; do

    echo -e "\n*** Installing Python package ${pkg} by pip ..."

    msg="\nDo you want to pip install ${pkg}"
    if [[ ! -z ${_MLHUB_OPTION_YES} ]] || _is_yes "${msg}"; then
      ${pip} install --root ${package_path}/.python ${pkg}
      _check_returncode
    fi

  done

elif [[ ${abbr} == 'con' ]]; then  # Install Python packages by conda

  # TODO: Add support for environment.yaml and specified channel

  category=$2
  shift

  if [[ ${category} == 'list' ]]; then  # conda install package

    for pkg in "$@"; do

      echo -e "\n*** Installing Python package ${pkg} by ${src} ..."

      msg="\nDo you want to ${src} install ${pkg}"
      if [[ ! -z ${_MLHUB_OPTION_YES} ]] || _is_yes "${msg}"; then
        ${src} install -y ${pkg}
        _check_returncode
      fi

    done

  elif [[ ${category} == 'file' ]]; then  # conda env create -f environment.yaml

    echo -e "\n*** Creating conda environment from $@ ..."

    msg="\nDo you want to continue"
    if [[ ! -z ${_MLHUB_OPTION_YES} ]] || _is_yes "${msg}"; then
      ${src} env create -f $@
      _check_returncode
    fi

  fi

else
  echo "*** Unknown source of required Python packages: $1" 1>&2
  exit 1
fi
