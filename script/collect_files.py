import os


def collect_files(source):
    """
    collects to files to be transfered
    could be files or dirs
    searches recursivly
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
            for filename in filenames:
                files.append(
                    os.path.join(root, filename)
                )

        files.sort()

        return files

    raise ValueError(
        f"Unsupported source: {source}"
    )
    """
    collects to files to be transfered
    could be files or dirs
    searches recursivly
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
            for filename in filenames:
                files.append(
                    os.path.join(root, filename)
                )

        files.sort()

        return files

    raise ValueError(
        f"Unsupported source: {source}"
    )
