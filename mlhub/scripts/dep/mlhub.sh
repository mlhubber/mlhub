#! /bin/bash -
# Check and install pre-requisites of MLHUB per se as well as bash completion scripts.

PREREQUISITES='
  r-base
  r-cran-devtools
  libxml2-dev
  pandoc
'

COMPLETION_SCRIPT=bash_completion.d/ml.bash
COMPLETION_INSTALL_PATH=/etc/bash_completion.d

# Install system dependencies

for pkg in ${PREREQUISITES}; do
  if ! dpkg-query -s ${pkg} 2>/dev/null | grep 'installed' > /dev/null; then
    echo -e "\n*** Installing the system package '${pkg}' ..."
    sudo apt-get install -y ${pkg}
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