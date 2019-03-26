#! /bin/bash -

source $(dirname $0)/utils.sh

src=$1
abbr=${src:0:3}
shift

if [[ ${abbr} == 'pyt' ]]; then

  # Install Python package from system

  if [[ -n "$@" ]]; then
    pkgs=$(echo "$@" | sed 's/[^ ]* */'"${src}"'-&/g')
    bash $(dirname $0)/system.sh ${pkgs}
    _check_returncode
  fi

elif [[ ${abbr} == 'pip' ]]; then

  # pip install package
  # TODO: Add support for version specification

  # For conda3, pip is pip3, and pip3 may not exist.
  old_src=${src}
  post=${src#pip}
  if [[ ! -z ${post} ]]; then
    if pip --version | grep -i "python ${post}" > /dev/null; then
      src=pip
    fi
  fi

  # Check if the packages are already installed

  local_pkgs=$(${src} list)  # List of installed pip packages
  for pkg in "$@"; do
    name=${pkg%%[>=<]*}
    installed_version=$(echo "${local_pkgs}" | grep "^${name} " | awk '{print $2}')
    if _is_version_satisfied "${pkg}" "${installed_version}"; then
      installedpkgs+=" ${pkg}"
    else
      pkgstoinstall+=" ${pkg}"
    fi
  done

  if [[ ! -z ${installedpkgs} ]]; then
    echo
    echo "*** The following required ${src} packages are already installed:"
    echo " ${installedpkgs}"
  fi

  for pkg in ${pkgstoinstall}; do
    echo
    echo "*** Installing Python package ${pkg} by ${old_src} ..."
    if [[ ! -z ${_MLHUB_OPTION_YES} ]] || _is_yes "\nDo you want to ${src} install ${pkg}"; then
      ${src} install ${pkg}
      _check_returncode
    fi
  done

elif [[ ${abbr} == 'con' ]]; then

  # Install Python packages by conda
  # TODO: Add support for environment.yaml and specified channel

  category=$2
  shift

  if [[ ${category} == 'list' ]]; then

    # conda install package

    for pkg in "$@"; do
      echo
      echo "*** Installing Python package ${pkg} by ${src} ..."
      if [[ ! -z ${_MLHUB_OPTION_YES} ]] || _is_yes "\nDo you want to ${src} install ${pkg}"; then
        ${src} install -y ${pkg}
        _check_returncode
      fi
    done

  elif [[ ${category} == 'file' ]]; then

    # conda env create -f environment.yaml

    echo
    echo "*** Creating conda environment from $@ ..."
    if [[ ! -z ${_MLHUB_OPTION_YES} ]] || _is_yes "\nDo you want to continue"; then
      ${src} env create -f $@
      _check_returncode
    fi

  fi

else
  echo "*** Unknown source of required Python packages: $1" 1>&2
  exit 1
fi
