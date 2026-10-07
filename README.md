# Lageos-Cluster-Paste
Paste (one) large file into restricted VNC-Connections that only allow to paste strings with less than 1000 characters. This script works by taking control of the clipboard.
Currently Linux only.


## INSTALLATION ##

-install Python (usually preinstalled on most Distros)

-install xclip and xdotool:

### Fedora
```bash	        
sudo dnf install xclip xdotool
```
### Debian/Ubuntu 
```bash	        
sudo apt install xclip xdotool
```
### Arch
```bash	        
sudo pacman -S xclip xdotool
```


clone repo: 
```bash
git clone https://github.com/AgentLageos/Lageos-Cluster-Paste.git
```	        

## Usage 

1. open VNC window
2. open console (this script is made for bash)
3. go to location where you want to copy your file

4. on your local machine run:

```bash
cd Lageos-Cluster-Paste/script
python lcp.py <path/to/file>
```


5. quickly switch to open VNC window AND (VERY IMPORTANT) left-click

6. Wait for finish.



## IMPORTANT

-Made for X11, might not work with Wayland.

-Stay inside VNC-Window while copying, otherwise file transfer will be interrupted.

-When starting the script a "Remote Control"-Window might appear asking for permission. Just quickly press ok.
If you where too slow pressing ok, you need to re-run, since the script won't wait for you to grant permission and won't check if the file was copied over completely.
However it will only ask you once for permission.






