#! /bin/bash -

_check_returncode() {

  # Check the return code of previous command and exit with specified return code if given.

  if [[ $? -ne 0 ]]; then
    if [[ $# -gt 0 ]]; then
      exit $1
    fi
    exit 1
  fi
}

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
