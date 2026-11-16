def read_file_chunks(file_name, chunk_size):
    with open(file_name, "rb") as f:
        while True:
            chunk = f.read(chunk_size)

            if not chunk:
                break

            yield chunk
