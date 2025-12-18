# Dependency Definitions

import importlib.util
import subprocess
import sys


REQUIRED_PACKAGES = {
    "requests": "requests",
    "folium": "folium",
    "ping3": "ping3",
    "scapy": "scapy"
}


def _is_installed(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _install_package(package_name: str) -> bool:
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", package_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def check_dependencies(interactive: bool = True) -> None:
    print("\nChecking dependencies:\n")

    for package, module in REQUIRED_PACKAGES.items():
        if _is_installed(module):
            print(f"   [OK] {package} found")
            continue

        print(f"   [MISSING] {package} not found")

        if not interactive:
            print(f"   Install '{package}' manually and try again.")
            sys.exit(1)

        choice = input(f"   Install '{package}' now? (yes/no): ").strip().lower()
        if choice not in ("yes", "y"):
            print(f"   Cannot continue without '{package}'. Exiting.")
            sys.exit(1)

        if _install_package(package):
            print(f"   '{package}' successfully installed")
        else:
            print(f"   Failed to install '{package}'. Install manually.")
            sys.exit(1)
