import logging
from typing import Dict, Optional, Union

from easyfs import File

from dcontainer.devcontainer.models.devcontainer_feature import FeatureOption
from dcontainer.devcontainer.models.devcontainer_feature_definition import (
    FeatureDependencies,
)
from dcontainer.settings import ENV_CLI_LOCATION, ENV_FORCE_CLI_INSTALLATION
from dcontainer.utils.version import resolve_own_release_version

logger = logging.getLogger(__name__)

RELEASE_LINK = """https://github.com/devcontainers-contrib/cli/releases/download/{RELEASE_VERSION}"""


DCONTAINER_SETUP_BASH_SCRIPT = """#!/bin/bash -i
# This code was generated by the dcontainer cli 
# For more information: https://github.com/devcontainers-contrib/cli 

set -e


ensure_curl() {{
    # Ensure curl available
    if ! type curl >/dev/null 2>&1; then
        apt-get update -y && apt-get -y install --no-install-recommends curl ca-certificates
    fi 
}}


ensure_dcontainer() {{
    # Ensure existance of the dcontainer cli program
    local variable_name=$1
    local dcontainer_location=""

    # If possible - try to use an already installed dcontainer
    if [[ -z "${{{force_cli_installation_env}}}" ]]; then
        if [[ -z "${{{cli_location_env}}}" ]]; then
            if type dcontainer >/dev/null 2>&1; then
                echo "Using a pre-existing dcontainer"
                dcontainer_location=dcontainer
            fi
        elif [ -f "${{{cli_location_env}}}" ] && [ -x "${{{cli_location_env}}}" ] ; then
            echo "Using a pre-existing dcontainer which were given in env varialbe"
            dcontainer_location=${{{cli_location_env}}}
        fi
    fi

    # If not previuse installation found, download it temporarly and delete at the end of the script 
    if [[ -z "${{dcontainer_location}}" ]]; then

        if [ "$(uname -sm)" == "Linux x86_64" ] || [ "$(uname -sm)" == "Linux aarch64" ]; then
            tmp_dir=$(mktemp -d -t dcontainer-XXXXXXXXXX)

            clean_up () {{
                ARG=$?
                rm -rf $tmp_dir
                exit $ARG
            }}
            trap clean_up EXIT

            curl -sSL {release_link}/dcontainer-"$(uname -m)"-unknown-linux-gnu.tgz | tar xfzv - -C "$tmp_dir"
            chmod a+x $tmp_dir/dcontainer
            dcontainer_location=$tmp_dir/dcontainer
        else
            echo "No binaries compiled for non-x86-linux architectures yet: $(uname -m)"
            exit 1
        fi
    fi

    # Expose outside the resolved location
    declare -g ${{variable_name}}=$dcontainer_location

}}

ensure_curl

ensure_dcontainer dcontainer_location

"""

SINGLE_DEPENDENCY = """$dcontainer_location \\
    install \\
    devcontainer-feature \\
    "{feature_oci}" \\
    {stringified_envs_args}
"""


class DependenciesSH(File):
    REF_PREFIX = "$options."

    def __init__(
        self,
        dependencies: Optional[FeatureDependencies],
        options: Optional[Dict[str, FeatureOption]],
        release_version: Optional[str] = None,
    ) -> None:
        self.release_version = release_version
        self.dependencies = dependencies
        self.options = options
        super().__init__(content=self.to_str().encode())

    @staticmethod
    def _escape_qoutes(value: str) -> str:
        return value.replace('"', '\\"')

    @staticmethod
    def is_param_ref(param_value: str) -> bool:
        return param_value.startswith(DependenciesSH.REF_PREFIX)

    def create_install_command(
        self, feature_oci: str, params: Dict[str, Union[str, bool]]
    ) -> str:
        stringified_envs_args = " ".join(
            [
                f'--option {env}="{DependenciesSH._escape_qoutes(str(val))}"'
                for env, val in params.items()
            ]
        )

        return SINGLE_DEPENDENCY.format(
            stringified_envs_args=stringified_envs_args, feature_oci=feature_oci
        )

    @staticmethod
    def resolve_param_ref(
        param_ref: str, options: Optional[Dict[str, FeatureOption]]
    ) -> str:
        if options is None:
            raise ValueError(
                f"option reference was given: '{param_ref}' but no options exists"
            )

        option_name = param_ref.replace(DependenciesSH.REF_PREFIX, "")

        option = options.get(option_name, None)
        if option is None:
            raise ValueError(
                f"could not resolve option reference: '{param_ref}' please ensure you spelled the option name right ({option})"
            )
        return f"${option_name}".upper()

    @staticmethod
    def _generate_dcontainer_setup_bash_script(release_version: str) -> str:
        return DCONTAINER_SETUP_BASH_SCRIPT.format(
            release_link=RELEASE_LINK.format(RELEASE_VERSION=release_version),
            force_cli_installation_env=ENV_FORCE_CLI_INSTALLATION,
            cli_location_env=ENV_CLI_LOCATION,
            RELEASE_VERSION=release_version,
        )

    def to_str(self) -> str:
        if self.dependencies is None or len(self.dependencies) == 0:
            return ""

        try:
            release_version = self.release_version or resolve_own_release_version()
        except Exception as e:
            raise ValueError(
                "could not resolve release version because of error, please manually set release_verison"
            ) from e

        installation_lines = []
        for feature_dependency in self.dependencies:
            resolved_params = {}
            for param_name, param_value in feature_dependency.options.items():
                if isinstance(param_value, str):
                    if DependenciesSH.is_param_ref(param_value):
                        param_value = DependenciesSH.resolve_param_ref(
                            param_value, self.options
                        )

                resolved_params[param_name] = param_value
            installation_lines.append(
                self.create_install_command(feature_dependency.feature, resolved_params)
            )
        dependency_installation_lines = "\n\n".join(installation_lines)
        return (
            DependenciesSH._generate_dcontainer_setup_bash_script(
                release_version=release_version
            )
            + dependency_installation_lines
        )
