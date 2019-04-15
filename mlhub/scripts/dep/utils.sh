#! /bin/bash -
# ----------------------------------------------------------------------
# Utilities frequently used throughout various scripts.
# ----------------------------------------------------------------------

_get_corresponding_pip() {
  local pyexe="${1}"
  local pipname="pip3"
  local pipexe="$(type -p ${pipname} 2>/dev/null)"

  if [[ -z ${pipexe} ]]; then
    pipname="pip"
  fi

  for x in $(type -ap ${pipname}); do
    local pippypath="$(grep "^#!" ${x} | head -1 | cut -d'!' -f2)"
    if [[ "${pippypath}" == "${pyexe}" ]]; then
      pipexe="${x}"
      break
    fi
  done

  echo "${pipexe}"
}

######################################################################
# Global variables
######################################################################

# Use system's version of pip, R and Rscript to unify the execution environment

bash='/bin/bash'

R='/usr/bin/R'
Rscript='/usr/bin/Rscript'

sys_python='/usr/bin/python3'
sys_pip='/usr/bin/pip3'

python="${_MLHUB_PYTHON_EXE}"
pip="$(_get_corresponding_pip ${python})"

R_SYS_PKG='r-base'
R_DEVTOOLS_SYS_PKG='r-cran-devtools'


######################################################################
# Version comparison
######################################################################

# Assume version number consists of three parts.

_major_version() {
  echo $(echo ${1} | awk -F '.' '{print $1}')
}

_minor_version() {
  echo $(echo ${1} | awk -F '.' '{print $2}')
}

_patch_version() {
  echo $(echo ${1} | awk -F '.' '{print $3}')
}

_compare_version_seg() {
  if [[ -z ${1} ]]; then
    echo '<'
  elif [[ -z ${2} ]]; then
    echo '>'
  elif [[ ${1} -gt ${2} ]]; then
    echo '>'
  elif [[ ${1} -lt ${2} ]]; then
    echo '<'
  else
    echo '='
  fi
}

_compare_version() {

  # Compare two versions composed of three segments.

  local first_major=$(_major_version ${1})
  local first_minor=$(_minor_version ${1})
  local first_patch=$(_patch_version ${1})

  local second_major=$(_major_version ${2})
  local second_minor=$(_minor_version ${2})
  local second_patch=$(_patch_version ${2})

  # Compare major version

  local result="$(_compare_version_seg "${first_major}" "${second_major}")"

  if [[ ${result} == '=' ]]; then

    # Compare minor version

    result="$(_compare_version_seg "${first_minor}" "${second_minor}")"

    if [[ ${result} == '=' ]]; then

      # Compare patch version

      result="$(_compare_version_seg "${first_patch}" "${second_patch}")"

    fi

  fi

  echo "${result}"
}

_is_version_satisfied() {

  # Given the description of version requirement and the installed version,
  # return whether it is satisfied.

  local requirement=${1}
  local installed_version=${2}

  local name=${requirement%%[>=<]*}
  local required_version=${requirement##*[>=<]}

  if [[ -z ${installed_version} ]]; then
    return 1
  elif [[ ${name} == ${required_version} ]]; then
    # name == version means no version specified.
    return 0
  else
    local require=${requirement#${name}}
    local require=${require%${required_version}}
    local actual="$(_compare_version ${installed_version} ${required_version})"
    local require_first=${require:0:1}
    local require_second=${require:1:1}
    if [[ ${require_first} == ${actual} ]]; then
      return 0
    elif [[ ! -z ${require_second} ]] && [[ ${actual} == '=' ]]; then
      return 0
    else
      return 1
    fi
  fi
}


######################################################################
# R related
######################################################################

_get_R_version() {
  echo "$(${R} --version | head -1 | cut -d' ' -f3)"
}

_get_r_base_version() {
  echo "$(apt-cache show --no-all-versions "${R_SYS_PKG}" 2>/dev/null | grep "^Version" | cut -d' ' -f2 | cut -d'-' -f1)"
}

_is_R_installed() {
  if ${R} --version 2>1 1>/dev/null; then
    return 0
  else
    return 1
  fi
}

######################################################################
# System related
######################################################################

_is_system_pkg_installed() {
  local pkg=${1}
  if dpkg-query -s ${pkg} 2>/dev/null | grep 'installed' > /dev/null; then
    return 0
  else
    return 1
  fi
}

_is_system_pkg_found() {

  # Check if there is a system package called $1

  local pkg=${1}
  if apt-cache show --no-all-versions ${pkg} 2>1 1>/dev/null; then
    return 0
  else
    return 1
  fi
}


######################################################################
# Python related
######################################################################

_get_pip_pkg_version() {
  local pkg=${1}
  echo "$(${pip} show ${pkg} 2>/dev/null | grep '^Version:' | cut -d' ' -f2)"
}


######################################################################
# Misc
######################################################################

_check_returncode() {

  # Check the return code of previous command and exit with specified return code if given.

  if [[ $? -ne 0 ]]; then
    if [[ $# -gt 0 ]]; then
      exit $1
    fi
    exit 1
  fi
}

_is_yes() {

  # Ask and get yes or no input.

  echo -ne "${1} [Y/n]? "
  read answer
  if [[ -z ${answer} ]] || [[ "${answer}" != "${answer#[Yy]}" ]]; then
    return 0
  else
    return 1
  fi
}
