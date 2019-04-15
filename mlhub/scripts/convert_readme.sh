#! /bin/bash -
# ----------------------------------------------------------------------
# This scrip is used for converting README into README.txt
# ----------------------------------------------------------------------

# Check if 'pandoc' is installed

#if ! dpkg-query -s pandoc 2>/dev/null | grep 'installed' > /dev/null; then
#    exit 5
#fi

# Conversion

set -o pipefail
pandoc -t plain ${1} | awk '/^Usage$$/{exit}{print}' | perl -00pe0 > ${2}

returncode=$?
if [[ ${returncode} -ne 0 ]]; then
  rm ${2}
  exit ${returncode}
fi
