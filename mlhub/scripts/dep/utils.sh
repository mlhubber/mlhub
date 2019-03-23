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

_r_version_newer_than() {

  # Check if a version is newer than the other one.

  local first_major=$(echo ${1} | cut -d'.' -f1)
  local first_minor=$(echo ${1} | cut -d'.' -f2)
  local first_patch=$(echo ${1} | cut -d'.' -f3)

  local second_major=$(echo ${2} | cut -d'.' -f1)
  local second_minor=$(echo ${2} | cut -d'.' -f2)
  local second_patch=$(echo ${2} | cut -d'.' -f3)

  if [[ ${first_major} -gt ${second_major} ]]; then
    return 0
  elif [[ ${first_major} -eq ${second_major} ]]; then
    if [[ ${first_minor} -gt ${second_minor} ]]; then
      return 0
    elif [[ ${first_minor} -eq ${second_minor} ]]; then
      if [[ ${first_patch} -gt ${second_patch} ]]; then
        return 0
      fi
    fi
  fi

  return 1
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
