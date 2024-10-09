import argparse
from pathlib import Path

from .configuration import load_config
from .layout import layout_from_directory


def parse_commandline() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Combine documents and images in a directory into a single PDF"
    )
    parser.add_argument(
        "directory",
        help="Directory where the files to combine are located",
        type=Path,
    )
    parser.add_argument(
        "output_file",
        help="Output filename (default: `%(default)s`)",
        default="out.pdf",
        nargs="?",
        type=Path,
    )
    parser.add_argument(
        "-c",
        "--config",
        help="Configuration file (default: `%(default)s`",
        default="config.toml",
        type=Path,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_commandline()

    directory = args.directory
    config = load_config(args.config)

    output_doc = layout_from_directory(directory, config)

    output_doc.ez_save(args.output_file)


if __name__ == "__main__":
    main()
