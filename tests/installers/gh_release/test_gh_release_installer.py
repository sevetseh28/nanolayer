from typing import List, Optional

import pytest
from helpers import execute_current_python_in_container


# @pytest.mark.skip(reason="not implemented yet")
@pytest.mark.parametrize(
    "test_command,excpected_result,image,repo,target,docker_platform",
    [
        (
            "upx --version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "upx/upx",
            "upx",
            "linux/amd64",
        ),
        (
            "doctl version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "digitalocean/doctl",
            "doctl",
            "linux/amd64",
        ),
        (  # classic
            "argocd --help",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "argoproj/argo-cd",
            "argocd",
            "linux/amd64",
        ),
        (  # alpine
            "argocd --help",
            0,
            "mcr.microsoft.com/devcontainers/base:alpine",
            "argoproj/argo-cd",
            "argocd",
            "linux/amd64",
        ),
        (  # arm
            "argocd --help",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "argoproj/argo-cd",
            "argocd",
            "linux/arm64",
        ),
        (  # two binaries at same repo
            "which kubectx",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "ahmetb/kubectx",
            "kubectx",
            "linux/amd64",
        ),
        (  # two binaries at same repo
            "which kubens",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "ahmetb/kubectx",
            "kubens",
            "linux/amd64",
        ),
        (  # control group for arm
            "terrascan version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "tenable/terrascan",
            "terrascan",
            "linux/amd64",
        ),
        (  # arm
            "terrascan version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "tenable/terrascan",
            "terrascan",
            "linux/arm64",
        ),
        (
            "gh --version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "cli/cli",
            "gh",
            "linux/amd64",
        ),
        (  # folder named btop in archive
            "btop --version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "aristocratos/btop",
            "btop",
            "linux/amd64",
        ),
        (  # zip archive for linux
            "exa --version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "ogham/exa",
            "exa",
            "linux/amd64",
        ),
        (  # .apk file
            "duf --version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "muesli/duf",
            "duf",
            "linux/amd64",
        ),
        (  # .pem file
            "caddy --version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "caddyserver/caddy",
            "caddy",
            "linux/amd64",
        ),
        (  # has positive "static"
            "cas --version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "codenotary/cas",
            "cas",
            "linux/amd64",
        ),
        (  # .sbom file
            "gitsign version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "sigstore/gitsign",
            "gitsign",
            "linux/amd64",
        ),
        (  # has negative "musl"
            "cyclonedx --version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "CycloneDX/cyclonedx-cli",
            "cyclonedx",
            "linux/amd64",
        ),
        (
            "pwsh --version",
            1,
            "mcr.microsoft.com/devcontainers/base:debian",
            "PowerShell/PowerShell",
            "pwsh",
            "linux/amd64",
        ),
    ],
)
def test_gh_release_install(
    test_command,
    excpected_result: int,
    image: str,
    repo: List[str],
    target: str,
    docker_platform: str,
) -> None:
    full_test_command = f"sudo PYTHONPATH=$PYTHONPATH python3 -m nanolayer install gh-release {repo} {target} && {test_command}"

    assert excpected_result == execute_current_python_in_container(
        test_command=full_test_command,
        image=image,
        docker_platform=docker_platform,
        nanolayer_version="v0.4.25",
    )
