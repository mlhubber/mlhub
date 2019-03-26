#! /bin/bash -
# Check and install pre-requisites of MLHUB per se as well as bash completion scripts.

source $(dirname $0)/utils.sh

PREREQUISITES='
  r-base
  r-cran-devtools
  libxml2-dev
  pandoc
  eom
  atril
'

R_DEVTOOLS_DEPS='
  libssl-dev
  libgit2-dev
'

COMPLETION_SCRIPT=bash_completion.d/ml.bash
COMPLETION_INSTALL_PATH=/etc/bash_completion.d

# Upgrade pip

echo -e "\n*** Checking if pip is the latest version ..."
if pip list -o 2>/dev/null | grep -e "^pip" > /dev/null; then
  if [[ ! -z ${_MLHUB_OPTION_YES} ]] || _is_yes "\nDo you want to upgrade pip"; then
    pip install --upgrade pip
  fi
fi

# Install system dependencies

echo -e "\n*** Updating package index which may ask password for root privilege ..."
sudo apt-get update

for pkg in ${PREREQUISITES}; do
  if ! dpkg-query -s ${pkg} 2>/dev/null | grep 'installed' > /dev/null; then

    echo -e "\n*** Installing the system package '${pkg}' ..."

    if [[ ${pkg} == 'r-base' ]] && R --version 2>/dev/null; then

      # Check if R is the newest version

      r_version=$(R --version | head -1 | cut -d' ' -f3)
      r_base_version=$(apt show r-base 2>/dev/null \
                      | grep "^Version" \
                      | cut -d' ' -f2 \
                      | cut -d'-' -f1)

      if [[ $(_compare_version ${r_base_version} ${r_version}) == '>' ]]; then
        if [[ ! -z ${_MLHUB_OPTION_YES} ]] || _is_yes "\nDo you want to install a newer version of R"; then
          sudo apt-get install -y ${pkg}
        fi
      else
        echo -e "\nThe installed R version is newer than in the repo."
      fi

    elif [[ ${pkg} == 'r-cran-devtools' ]] \
         && ! dpkg-query -s ${pkg} 2>/dev/null ; then

      # Try to install devtools from within R if r-cran-tools not available

      echo -e "\n${pkg} is not available! Trying to install 'devtools' from CRAN ..."
      if [[ ! -z ${_MLHUB_OPTION_YES} ]] || _is_yes "\nDo you want to install 'devtools' from CRAN"; then
        for dep in ${R_DEVTOOLS_DEPS}; do
          if [[ ! -z ${_MLHUB_OPTION_YES} ]] || _is_yes "\nDo you want to install '${dep}' required by 'devtools'"; then
            sudo apt-get install -y ${dep}
            _check_returncode
          fi
        done

        Rscript -e 'lib <- Sys.getenv("R_LIBS_USER"); dir.create(lib, showWarnings=FALSE, recursive=TRUE); install.packages("devtools", repos="https://cloud.r-project.org", lib=lib)'
      fi

    else
      if [[ ! -z ${_MLHUB_OPTION_YES} ]] || _is_yes "\nDo you want to install '${pkg}'"; then
        sudo apt-get install -y ${pkg}
      fi
    fi

    _check_returncode

  fi
done

# Configure bash completion

COMMANDS=(
  "sudo install -m 0644 ${COMPLETION_SCRIPT} ${COMPLETION_INSTALL_PATH}"
  "ml available > /dev/null"
  "ml installed > /dev/null"
)

echo -e '\n*** Configuring bash completion which may ask password for root privilege ...'
if [[ ${COMPLETION_SCRIPT} -nt ${COMPLETION_INSTALL_PATH}/${COMPLETION_SCRIPT##*/} ]]; then
  for cmd in "${COMMANDS[@]}"; do
    echo "Executing: " "${cmd}"
    bash -c "${cmd}"
  done
  echo 'Done'
fi

echo -e "\nFor tab completion to take immediate effect:"
echo -e "\n  $ source ${COMPLETION_INSTALL_PATH}/${COMPLETION_SCRIPT##*/}\n"
