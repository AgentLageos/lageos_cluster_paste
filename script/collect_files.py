import os

from script.state import STATE_FILE_NAME

GIT_DIR_NAME = ".git"
GIT_FILE_NAMES = {
    ".gitignore",
    ".gitattributes",
    ".gitmodules",
}

#a dir containing this file is skipped with all its contents
BLOCK_FILE_NAME = ".lcp_block"


def collect_files(source, exclude_git=True):
    """
    collects to files to be transfered
    could be files or dirs
    searches recursivly
    exclude_git: skip .git dirs and git config files
    dirs containing BLOCK_FILE_NAME are skipped completely
    """

    source = os.path.abspath(source)

    if not os.path.exists(source):
        raise FileNotFoundError(
            f"Source does not exist: {source}"
        )

    if os.path.isfile(source):
        return [source]

    if os.path.isdir(source):
        files = []

        for root, dirs, filenames in os.walk(source):
            if BLOCK_FILE_NAME in filenames:
                #prune in place so os.walk does not descend
                dirs[:] = []
                continue

            if exclude_git:
                dirs[:] = [d for d in dirs if d != GIT_DIR_NAME]

            for filename in filenames:
                if filename == STATE_FILE_NAME:
                    continue
                if exclude_git and filename in GIT_FILE_NAMES:
                    continue
                files.append(
                    os.path.join(root, filename)
                )

        files.sort()

        return files

    raise ValueError(
        f"Unsupported source: {source}"
    )
