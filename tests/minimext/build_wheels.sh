#!/bin/bash -e
# Copyright (C) 2024 Stewart Miles
# Licensed to the Python Software Foundation under a contributor agreement.
# See LICENSE.txt and CONTRIBUTORS.txt.

readonly DEFAULT_PYTHON_VERSION="$(python --version |
                                     cut -d ' ' -f 2 |
                                     cut -d. -f 1,2)"
readonly DEFAULT_PYTHON_VERSIONS="2.7 3.5 ${DEFAULT_PYTHON_VERSION}"


help() {
  echo "\
Builds Linux wheels for this package using a range of Python distributions.

This script requires a Ubuntu distribution and will leave the deadsnakes PPA
https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa
and Python packages used by this script installed.

$(basename "$0") [-d] [-I] [-S] [-p versions] [-h]

-d: Enable dry run mode, simply display rather than execute commands.
-S: Disable Python PPA installation.
-I: Disable Python apt package installation
-p: Space separated list of Python versions to install and build wheels for.
    This defaults to \"${DEFAULT_PYTHON_VERSIONS}\".
-h: Display this help.
"
  exit 1
}

main() {
  readonly THIS_DIRECTORY="$(cd "$(dirname "${0}")"; pwd)"
  local dryrun=
  local install_python=1
  local install_python_ppa=1
  local selected_python_versions="${DEFAULT_PYTHON_VERSIONS}"

  while getopts "dhISp:" OPTION; do
    # shellcheck disable=SC2209
    case "${OPTION}" in
      d) dryrun=echo
         ;;
      I) install_python=0
         ;;
      S) install_python_ppa=0
         ;;
      p) selected_python_versions="${OPTARG}"
         ;;
      h|*) help
         ;;
    esac
  done

  IFS=' ' read -r -a python_versions <<< "${selected_python_versions}"

  if [[ $((install_python_ppa)) -eq 1 ]]; then
    set -x
    ${dryrun} sudo add-apt-repository ppa:deadsnakes/ppa
    set +x
  fi

  if [[ $((install_python)) -eq 1 ]]; then
    # shellcheck disable=SC2207
    readonly -a PYTHON_APT_PACKAGES=(
      $(for version in "${python_versions[@]}"; do
          echo "python${version}-dev";
        done))
    set -x
    ${dryrun} sudo apt install "${PYTHON_APT_PACKAGES[@]}"
    set +x
  fi

  local wheels_directory="${THIS_DIRECTORY}/wheels"
  mkdir -p "${wheels_directory}"

  local venv_directory
  local versioned_python
  local version
  for version in "${python_versions[@]}"; do
    versioned_python="python${version}"
    venv_directory="${THIS_DIRECTORY}/.venv${version}"

    # Try to bootstrap pip if it isn't found.
    if ! ${dryrun} "${versioned_python}" -c "import pip" 2> /dev/null; then
      # shellcheck disable=SC2155
      local temporary_directory="$(mktemp -d)"
      local get_pip="${temporary_directory}/get-pip-${version}.py"
      ${dryrun} curl --output "${get_pip}" \
           "https://bootstrap.pypa.io/pip/${version}/get-pip.py"
      ${dryrun} "${versioned_python}" "${get_pip}"
      rm -rf "${temporary_directory}"
    fi

    # Install virtualenv as venv isn't available in all Python versions.
    ${dryrun} "${versioned_python}" -m pip install virtualenv
    ${dryrun} "${versioned_python}" -m virtualenv "${venv_directory}"
    (
      cd "${THIS_DIRECTORY}"
      ${dryrun} source "${venv_directory}/bin/activate"
      # Upgrade pip and setuptools.
      ${dryrun} pip install -U pip
      ${dryrun} pip install -U setuptools
      # Build wheels to the wheels subdirectory.
      for embed_extension_metadata in 0 1; do
        set -x
        MINIMEXT_EMBED_EXTENSIONS_METADATA=${embed_extension_metadata} \
          ${dryrun} pip wheel . -w "${wheels_directory}"
        set +x
      done
    )
  done

  cp "${wheels_directory}"/*.whl "${THIS_DIRECTORY}/.."
}

main "$@"
