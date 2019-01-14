#! /bin/bash -

src=$1
abbr=${src:0:3}
shift

_check_returncode() {

  # Check the return code of previous command and exit with specified return code if given.

  if [[ $? -ne 0 ]]; then
    if [[ $# -gt 0 ]]; then
      exit $1
    fi
    exit 1
  fi
}


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

  sudo ${src} install --upgrade ${src}
  for pkg in "$@"; do
    echo
    echo "*** Installing Python package ${pkg} by ${old_src} ..."
    ${src} install ${pkg}
    _check_returncode
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
      ${src} install -y ${pkg}
      _check_returncode
    done

  elif [[ ${category} == 'file' ]]; then

    # conda env create -f environment.yaml

    echo
    echo "*** Creating conda environment from $@ ..."
    ${src} env create -f $@
    _check_returncode

  fi

else
  echo "*** Unknown source of required Python packages: $1" 1>&2
  exit 1
fi
