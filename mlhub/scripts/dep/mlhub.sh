#! /bin/bash -
# Check and install pre-requisites of MLHUB per se as well as bash completion scripts.

PREREQUISITES='
  r-base
  r-cran-devtools
  libxml2-dev
  pandoc
'

R_DEVTOOLS_DEPS='
  libssl-dev
  libgit2-dev
'

COMPLETION_SCRIPT=bash_completion.d/ml.bash
COMPLETION_INSTALL_PATH=/etc/bash_completion.d

_check_returncode() {

  # Check the return code of previous command and exit with specified return code if given.

  if [[ $? -ne 0 ]]; then
    if [[ $# -gt 0 ]]; then
      exit $1
    fi
    exit 1
  fi
}

# Install system dependencies

sudo apt-get update

for pkg in ${PREREQUISITES}; do
  if ! dpkg-query -s ${pkg} 2>/dev/null | grep 'installed' > /dev/null; then

    echo -e "\n*** Installing the system package '${pkg}' ..."
    sudo apt-get install -y ${pkg}

    if [[ $? -ne 0 ]]; then
      if [[ ${pkg} == 'r-cran-devtools' ]]; then

        # Try to install devtools from within R if c-cran-tools cannot be installed

        for dep in ${R_DEVTOOLS_DEPS}; do
          sudo apt-get install -y ${dep}
          _check_returncode
        done

        Rscript -e 'lib <- Sys.getenv("R_LIBS_USER"); dir.create(lib, showWarnings=FALSE, recursive=TRUE); install.packages("devtools", lib=lib)'
        _check_returncode

      else
        exit 1
      fi
    fi

  fi
done

# Configure bash completion

COMMANDS=(
  "sudo install -m 0644 ${COMPLETION_SCRIPT} ${COMPLETION_INSTALL_PATH}"
  "ml available > /dev/null"
  "ml installed > /dev/null"
)

if [[ ${COMPLETION_SCRIPT} -nt ${COMPLETION_INSTALL_PATH}/${COMPLETION_SCRIPT##*/} ]]; then
    echo -e '\n*** Configuring bash completion which may ask password for root privilege ...'
    for cmd in "${COMMANDS[@]}"; do
      echo "Executing: " "${cmd}"
      bash -c "${cmd}"
    done
    echo 'Done'
fi

echo -e "\nFor tab completion to take immediate effect:"
echo -e "\n  $ source ${COMPLETION_INSTALL_PATH}/${COMPLETION_SCRIPT##*/}\n"