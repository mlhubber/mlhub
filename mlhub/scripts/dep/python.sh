#! /bin/bash -

src=$1
abbr=${src:0:3}
shift

if [[ ${abbr} == 'pyt' ]]; then

  if [[ -n "$@" ]]; then
    pkgs=$(echo "$@" | sed 's/[^ ]* */'"${src}"'-&/g')
    bash $(dirname $0)/system.sh ${pkgs}
    if [[ $? -ne 0 ]]; then
      exit 1
    fi
  fi

elif [[ ${abbr} == 'pip' ]]; then

  # TODO: Add support for version specification

  # For conda3, pip is pip3, and pip3 may not exist.
  post=${src#pip}
  if [[ ! -z ${post} ]]; then
    if pip --version | grep -i "python ${post}" > /dev/null; then
      src=pip
    fi
  fi

  sudo ${src} install --upgrade ${src}
  for pkg in "$@"; do
    echo
    echo "*** Installing Python package ${pkg} by ${src}${post} ..."
    ${src} install ${pkg}
    if [[ $? -ne 0 ]]; then
      exit 1
    fi
  done

elif [[ ${abbr} == 'con' ]]; then

  # Install Python packages by conda
  # TODO: Add support for environment.yaml and specified channel

  for pkg in "$@"; do
    echo
    echo "*** Installing Python package ${pkg} by ${src} ..."
    ${src} install -y ${pkg}
    if [[ $? -ne 0 ]]; then
      exit 1
    fi
  done

else
  echo "*** Unknown source of required Python packages: $1" 1>&2
  exit 1
fi
