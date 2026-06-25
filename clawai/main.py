from clawai.core.config.config_manager import ConfigManager
from clawai.core.config.loaders import YamlLoader


def main() -> None:
    manager = ConfigManager(
        loader=YamlLoader("configs/config.yaml"),
    )

    manager.load()

    print(manager.all())


if __name__ == "__main__":
    main()