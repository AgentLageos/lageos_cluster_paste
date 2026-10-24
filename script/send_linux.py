import subprocess

def send_linux(text):
    p = subprocess.Popen(
        ['xclip', '-selection', 'clipboard'],
        stdin=subprocess.PIPE
    )
    p.communicate(input=text.encode())

    subprocess.run([
        'xdotool',
        'key',
        '--clearmodifiers',
        'ctrl+shift+v'
    ])
