#! /bin/bash -
# ----------------------------------------------------------------------
# This script is used for installing pre-requisites of MLHub per se,
# as well as bash completion scripts for MLHub.
# ----------------------------------------------------------------------

source $(dirname $0)/utils.sh

PREREQUISITES="
  ${R_SYS_PKG}
  ${R_DEVTOOLS_SYS_PKG}
  libxml2-dev
  pandoc
  eom
  atril
  git
"

R_DEVTOOLS_DEPS='
  libssl-dev
  libgit2-dev
'

COMPLETION_SCRIPT=bash_completion.d/ml.bash
COMPLETION_INSTALL_PATH=/etc/bash_completion.d

######################################################################
# Upgrade pip if possible
######################################################################

echo -e "\n*** Checking if pip is the latest version ..."

# TODO: Need to find a fast way to figure out if pip is the newest version

pip_version=$(${pip} list -o 2>/dev/null | grep -e "^pip")

if [[ ! -z ${pip_version} ]]; then
  old_pip_version=$(echo ${pip_version} | awk '{ print $2 }')
  new_pip_version=$(echo ${pip_version} | awk '{ print $3 }')
  msg="\nDo you want to upgrade pip from ${old_pip_version} to ${new_pip_version}"
  if [[ ! -z ${_MLHUB_OPTION_YES} ]] || _is_yes "${msg}"; then
    echo "Upgrading pip ..."
    ${pip} install --upgrade pip
  else
    echo "Keep pip as it is."
  fi
else
  echo -e "\npip is already the newest."
fi

######################################################################
# Install system dependencies
######################################################################

echo -e "\n*** Updating package index which may ask for a password for admin privileges ...\n"
sudo apt-get update

for pkg in ${PREREQUISITES}; do
  if ! _is_system_pkg_installed ${pkg}; then

    echo -e "\n*** Installing the system package '${pkg}' ..."

    if [[ ${pkg} == "${R_SYS_PKG}" ]] && _is_R_installed; then

      # R is already installed, so check if R is the newest version

      r_version="$(_get_R_version)"
      r_base_version="$(_get_r_base_version)"

      if [[ $(_compare_version ${r_base_version} ${r_version}) == '>' ]]; then
        msg="\nDo you want to install a newer version of R"
        if [[ ! -z ${_MLHUB_OPTION_YES} ]] || _is_yes "${msg}"; then
          sudo apt-get install -y ${pkg}
        fi
      else
        echo -e "\nThe installed R version is already newer than in the repo."
      fi

    elif [[ ${pkg} == "${R_DEVTOOLS_SYS_PKG}" ]]; then

      sudo apt-get install -y ${pkg}

      if [[ $? -ne 0 ]]; then

        # Try to install devtools from within R if r-cran-tools not available

        echo -e "\n${pkg} is not available! Trying to install 'devtools' from CRAN ..."

        msg="\nDo you want to install 'devtools' from CRAN"
        if [[ ! -z ${_MLHUB_OPTION_YES} ]] || _is_yes "${msg}"; then

          for dep in ${R_DEVTOOLS_DEPS}; do
            msg="\nDo you want to install '${dep}' required by 'devtools'"
            if [[ ! -z ${_MLHUB_OPTION_YES} ]] || _is_yes "${msg}"; then
              sudo apt-get install -y ${dep}
              _check_returncode
            fi
          done

          commands='lib <- Sys.getenv("R_LIBS_USER"); '
          commands+='dir.create(lib, showWarnings=FALSE, recursive=TRUE); '
          commands+='install.packages("devtools", repos="https://cloud.r-project.org", lib=lib)'

          echo -e "\nInstalling 'devtools' from CRAN ..."

          ${Rscript} -e "${commands}"

        fi

      fi

    else

      msg="\nDo you want to install '${pkg}'"
      if [[ ! -z ${_MLHUB_OPTION_YES} ]] || _is_yes "${msg}"; then
        sudo apt-get install -y ${pkg}
      fi

    fi

    _check_returncode

  fi
done

######################################################################
# Add specific R packages - Use sudo for now to system install it.
######################################################################

echo -e '\n*** Ensuring mlhub R package is installed - requires admin privileges ...'
sudo Rscript -e 'devtools::install_github("mlhubber/mlhub", quiet=TRUE)'

######################################################################
# Configure bash completion
######################################################################

COMMANDS=(
  "sudo install -m 0644 ${COMPLETION_SCRIPT} ${COMPLETION_INSTALL_PATH}"
  "ml available > /dev/null"
  "ml installed > /dev/null"
)

echo -e '\n*** Configuring bash completion - may require password for admin privileges ...\n'
if [[ ${COMPLETION_SCRIPT} -nt ${COMPLETION_INSTALL_PATH}/${COMPLETION_SCRIPT##*/} ]]; then
  for cmd in "${COMMANDS[@]}"; do
    echo "Executing:" "${cmd}"
    bash -c "${cmd}"
  done
  echo 'Done'
fi

echo -e "\nFor tab completion to take immediate effect:"
echo -e "\n  $ source ${COMPLETION_INSTALL_PATH}/${COMPLETION_SCRIPT##*/}\n"
