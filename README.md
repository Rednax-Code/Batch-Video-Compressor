# Batch Video Compressor
Exactly what the name suggests.

You select videos, set a target bitrate, set an output folder and run.
The rest is done for you.

### Usage
First open up your terminal of choice and launch the program.

If you are in the folder containing main.py, this can be done with:
```
py main.py
```

Now it should show something like this (or similar):
```
ID | Filename | Extension | Size | Duration | Bitrate | Selected |
0  | .git     | Folder

C:\Batch-Video-Compressor >>
```

From here, you can run the following commands:
- `cd [path]` This is used as you'd expect from a regular terminal.
Paths with spaces like "C:/Program Files" normally require the quotation marks, but it is not necessary here.
- `add [ID]` Adds video to selection by ID shown in the directory view.
- `addall` Adds all videos in current folder to selection.
- `remove [ID]` Removes video from selection by ID.
- `removeall` : removes all videos from selection.
- `view` Shows the file names of all selected videos.
- `bitrate [int/str]` Sets the target bitrate after compression in kbps or one of the following: 'low', 'medium', 'high'. These are presets (yet to be) set by me.
- `output [ID/path]` Sets the output folder by either ID, relative or absolute path.
- `run` Shows the selected videos, target bitrate and output path. Then prompts confirmation after which the compression will start.
- `quit` Quits the program.
- `exit` Equivalent to quit.
- `help` Shows a simplified version of this list.