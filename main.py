from clawai.application import Application
from clawai.bootstrap import build_container


def main() -> None:

    container = build_container()

    app = Application(container)

    app.initialize()

    print("ClawAI initialized successfully.")


if __name__ == "__main__":
    main()