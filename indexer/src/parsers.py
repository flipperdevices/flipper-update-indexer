import logging
import copy

from .models import *
from .channels import *
from .storage import storage


def add_files_to_version(
    version: Version, file_parser: FileParser, main_dir: str, channel_dir: str
) -> Version:
    """
    Method for adding a new artifact model to the selected version
    Args:
        version:
        file_parser:
        main_dir:
        channel_dir:

    Returns:
        Modified model version in which the file model was added
    """
    for cur in sorted(storage.list_files(main_dir, channel_dir)):
        # skip hidden files such as .DS_Store and the .version_id marker
        if cur.startswith("."):
            continue
        parsed_file = file_parser()
        try:
            parsed_file.parse(cur)
        except Exception as e:
            logging.exception(e)
            continue
        version.add_file(
            VersionFile(
                url=storage.public_url(main_dir, channel_dir, cur),
                target=parsed_file.target,
                type=parsed_file.type,
                sha256=storage.sha256(main_dir, channel_dir, cur),
            )
        )
    return version


def parse_dev_channel(
    channel: Channel,
    directory: str,
    file_parser: FileParser,
    indexer_github: IndexerGithub,
) -> Channel:
    """
    Method for creating a new version with a file
    and adding it to the dev channel
    Args:
        channel: Channel model (-> dev)
        directory: Save directory
        file_parser: The method by which the file piercing will take place (qFlipper, FileParser)

    Returns:
        New channel with added version
    """
    version = indexer_github.get_dev_version()
    version = add_files_to_version(version, file_parser, directory, "dev")
    channel.add_version(version)
    return channel


def parse_release_channel(
    channel: Channel,
    directory: str,
    file_parser: FileParser,
    indexer_github: IndexerGithub,
) -> Channel:
    """
    Method for creating a new version with a file
    and adding it to the release channel
    Args:
        channel: Channel model (-> release)
        directory: Save directory
        file_parser: The method by which the file piercing will take place (qFlipper, FileParser)

    Returns:
        New channel with added version
    """
    version = indexer_github.get_release_version()
    if version:
        version = add_files_to_version(version, file_parser, directory, version.version)
        channel.add_version(version)
    return channel


def parse_rc_channel(
    channel: Channel,
    directory: str,
    file_parser: FileParser,
    indexer_github: IndexerGithub,
) -> Channel:
    """
    Method for creating a new version with a file
    and adding it to the rc channel
    Args:
        channel: Channel model (-> release-candidate)
        directory: Save directory
        file_parser: The method by which the file piercing will take place (qFlipper, FileParser)

    Returns:
        New channel with added version
    """
    version = indexer_github.get_rc_version()
    if version:
        version = add_files_to_version(version, file_parser, directory, version.version)
        channel.add_version(version)
    return channel


def parse_github_channels(
    directory: str, file_parser: FileParser, indexer_github: IndexerGithub
) -> dict:
    """
    Method for creating a new index with channels
    Args:
        directory: Save directory
        file_parser: The method by which the file piercing will take place (qFlipper, FileParser)

    Returns:
        New index with added channels
    """
    json = Index()
    json.add_channel(
        parse_dev_channel(
            copy.deepcopy(development_channel), directory, file_parser, indexer_github
        )
    )
    json.add_channel(
        parse_release_channel(
            copy.deepcopy(release_candidate_channel),
            directory,
            file_parser,
            indexer_github,
        )
    )
    json.add_channel(
        parse_rc_channel(
            copy.deepcopy(release_channel), directory, file_parser, indexer_github
        )
    )
    return json.dict()
