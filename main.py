"""Convenience helper that prints instructions for running the Streamlit app."""


def main() -> None:
    print(
        "Launch the spectral analysis interface with:\n"
        "  streamlit run -m spectral_app.interface.streamlit_app"
    )


if __name__ == "__main__":
    main()
