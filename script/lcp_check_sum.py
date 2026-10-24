from script.check_args import check_args
from script.collect_files import collect_files



def transefer_checksum(
        path_to_file: str,
        base_path: str,
        chunk_size: int,
        paste_delay: float
):
    path_to_file = os.path.abspath(path_to_file)
    base_path = os.path.abspath(base_path)
    relative_path = Path(os.path.relpath(path_to_file, base_path))

    remote_file = relative_path.as_posix()

    clear_counter = 0
    
    if remote_dir:
        

def main():
    
    path_to_config = "script/config.yml"
    validate_config(path_to_config)
    config = load_config(path_to_config)
    chunk_size = config["chunk_size"]
    paste_delay = config["paste_delay"]

    source = check_args()
    
    files = collect_files(source)

    if not files:
        print("ERROR: No files found.")
        sys.exit(1)

        

    RAW_chunk_size = (chunk_size // 4) * 3

    if os.path.isfile(source):
        base_path = os.path.dirname(source)
    else:
        base_path = os.path.dirname(source)
    send("\n")
    print()
    print("Switch NOW to VNC Window...")

    for i in range(5, 0, -1):
        print(i)
        time.sleep(1)

    print()
    print("Starting...")
