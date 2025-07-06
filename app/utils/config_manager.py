import os

import yaml


class ConfigManager:
    """
    Config manager

    This class is responsible for managing the configuration of the web3 service.
    It is used to get the selected network, the networks, the assets and
    the rpc url for a given network.
    It is also used to get the asset config for a given asset and network.
    """

    def __init__(self):
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        config_path = os.path.join(project_root, "config.yaml")

        with open(config_path, "r") as file:
            config = yaml.safe_load(file)

        self.config = config

    def get_current_network(self) -> str:
        """Returns the selected network on the config file"""
        return self.config["current_network"]

    def get_networks(self) -> list[str]:
        """Returns the networks on the config file"""
        return self.config["networks"].keys()

    def get_assets(self) -> list[str]:
        """Returns the assets on the config file"""
        return self.config["assets"].keys()

    def get_native_asset(self) -> str:
        """Returns the native asset on the config file"""
        return self.config["native_asset"]

    def get_rpc_url(self, network: str) -> str:
        """Returns the rpc url for a given network"""
        if network not in self.get_networks():
            raise ValueError(f"Network {network} not found in config")
        return self.config["networks"][network]

    def get_asset(self, asset: str) -> dict[str, str]:
        """Returns the asset config for a given asset"""
        if asset not in self.get_assets():
            raise ValueError(f"Asset {asset} not found in config")
        return self.config["assets"][asset]
