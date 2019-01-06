#! /bin/bash -

src=$1
abbr=${src:0:3}
shift

if [[ ${abbr} == 'pyt' ]]; then

  for pkg in "$@"; do
    dep=${src}-${pkg}
    echo
    echo "*** Installing system Python package ${dep} ..."
    sudo apt-get install -y ${dep}
  done

elif [[ ${abbr} == 'pip' ]]; then

  # TODO: Add support for version specification

  sudo ${src} install --upgrade ${src}
  for pkg in "$@"; do
    echo
    echo "*** Installing Python package ${pkg} by ${src} ..."
    ${src} install ${pkg}
  done

elif [[ ${abbr} == 'con' ]]; then

  # Install Python packages by conda
  # TODO: Add support for environment.yaml and specified channel

  for pkg in "$@"; do
    echo
    echo "*** Installing Python package ${pkg} by ${src} ..."
    ${src} install -y ${pkg}
  done

else
  echo "*** Unknown source of required Python packages: $1" 1>&2
  exit 1
fi