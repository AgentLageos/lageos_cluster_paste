# Lageos-Cluster-Paste
Paste entire directories (or just one file) into restricted VNC-Connections that only allow to paste strings with less than X characters. This script works by taking control of the clipboard.
Made for Linux and Windows.


## INSTALLATION Linux##

-install Python (usually preinstalled on most Distros)

-install xclip and xdotool:

### Fedora
```bash	        
sudo dnf install xclip xdotool python3-pyyaml
```
### Debian/Ubuntu 
```bash	        
sudo apt install xclip xdotool python3-yaml
```
### Arch
```bash	        
sudo pacman -S xclip xdotool python-yaml
```

clone repo: 
```bash
git clone https://github.com/AgentLageos/Lageos-Cluster-Paste.git
```	        
## INSTALLATION Windows##

-install Python

-press WIN + R 
-type "cmd"
-press ENTER
-in Terminal type

```bash
pip install pyyaml
```

-download repo as zip and unpack

-or (recommended) clone repo: 
```bash
git clone https://github.com/AgentLageos/Lageos-Cluster-Paste.git
```	        

## Usage 

1. open VNC window
2. open console (this script is made for bash)
3. go to location where you want to copy your file

4. on your local machine run:

```bash
cd Lageos-Cluster-Paste
python lcp.py <path/to/file>
```


5. quickly switch to open VNC window AND (VERY IMPORTANT) left-click

   To abort a running transfer, click any other window (e.g. your local terminal).
   The script notices that the VNC window lost focus and stops before the next paste.
   (Ctrl+C does not work: while the script runs, the VNC window has focus, so Ctrl+C goes to the remote side.)

6. Wait for finish. Your local terminal shows a progress bar over all files:

```
[2/5] [#############-----------------]  43.39% | file  56.25% | elapsed 1m12s | ETA 1m34s
```

`[2/5]` is the current file, the bar shows the overall progress (in bytes), `file` the progress of the current file.
The ETA is estimated from the average speed so far.

7. Check the VNC terminal: every file is verified (SHA-256) on the remote side.
It shows either `DONE - ALL OK` or a list of failed files plus a command like:

```bash
python lcp.py --retry 2 5
```

Run it on your local machine to re-send only the failed files (the numbers refer to the last run).
This hint can be turned off with `retry_hint: false` in `script/config.yml`.

Git files (`.git` directories, `.gitignore`, `.gitattributes`, `.gitmodules`) are not sent when transferring a directory. To send them anyway, set `exclude_git: false` in `script/config.yml`.

To block a directory from being sent, put an (empty) file named `.lcp_block` into it. The directory and everything inside it, including subdirectories, is skipped:

```bash
touch ./my_project/build/.lcp_block
```

Requires `sha256sum` on the remote machine (part of coreutils). If it is missing, all files are reported as failed.

## Transferring a directory again

When a directory is transferred, a `.lcp_state.json` is saved inside the local directory.
It stores the checksums of all files that were sent (it is never sent itself).
On the next transfer of the same directory only new and changed files are sent:

```bash
python lcp.py ./my_project          # only changed files
python lcp.py --force ./my_project  # everything again
```

- Files that only exist on the remote side are left untouched. Files deleted locally are not deleted remotely.
- The state only knows what was *sent*. Use `--force` when transferring to a different remote location,
  when files were changed on the remote side, or when a transfer failed and was not re-sent with `--retry`.
- You may want to add `.lcp_state.json` to the `.gitignore` of your project.



## IMPORTANT INFO FOR LINUX

-Made for X11, might not work with Wayland.

-Stay inside VNC-Window while copying, otherwise file transfer will be interrupted.

-When starting the script a "Remote Control"-Window might appear asking for permission. Just quickly press ok.
If you were too slow pressing ok, the first files will be reported as failed at the end, just re-send them with the shown `--retry` command.
However it will only ask you once for permission.
