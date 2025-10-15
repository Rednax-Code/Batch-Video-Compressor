"""
Small program that automates the compression of a large number of video files to a target bitrate.
Made by Xander de Haan
"""

import ffmpeg

import os
import time
import threading
import tempfile

# Directory View Options
MAX_FILENAME_LEN = 20
PROGRESS_BAR_LEN = 40
VISIBLE_EXTENSIONS = {'mp4'}

# Exit Codes
OK = 0
ERR_CMD_NOT_FOUND = 1
ERR_DIR_NOT_FOUND = 2
ERR_INVALID_ARG = 3
ERR_ALREADY_SELECTED = 4
ERR_NOT_IN_SELECTION = 5
ERR_NO_VIDEOS_SELECTED = 6
ERR_NO_TARGET_BITRATE = 7
ERR_NO_OUTPUT_PATH = 8
ERR_FILE_IS_NOT_FOLDER = 9
ERR_WTF = 1000

CONTINUE_MESSAGE = '\nPress \'enter\' to continue\n'


class dir_item:
	ID: int
	name: str
	path: str
	is_file: bool
	extension: str
	size: int
	duration: int
	bitrate: int
	is_selected: bool = False

def clean_argument(arg):
	if isinstance(arg, list):
		str_arg = ''
		for i in range(len(arg)):
			str_arg += arg[i].strip('"').strip("'")
			if i != len(arg)-1:
				str_arg += ' '
		arg = str_arg
	return arg

def filter_relevant_content(path):
	"""Filters away irrelevant files"""
	folder_contents = os.listdir(path)
	relevant_content = []
	for item in folder_contents:
		item_path = os.path.join(path, item)
		if os.path.isdir(item_path):
			relevant_content.append(item)
		elif os.path.isfile(item_path):
			if item.split('.')[-1].lower() in VISIBLE_EXTENSIONS:
				relevant_content.append(item)
		else:
			print("What... how??")
	return relevant_content

def monitor_compression_progress(temp_file, text_base, total_frames):
	last_frame = 0
	while True:
		# Read current progress status
		if os.path.isfile(temp_file):
			with open(temp_file, 'r') as f:
				lines = f.readlines()
				for line in lines:
					if line.startswith('frame='):
						last_frame = int(line.split('=')[1])
					elif line.startswith('progress=end'):
						print(f'\r{text_base} {" ":<{PROGRESS_BAR_LEN}}  ', end='')
						print(f'\r{text_base} ✓')
						return
		
		# Update progress bar
		progress_bar = '#' * round(PROGRESS_BAR_LEN * last_frame / total_frames)
		print(f'\r{text_base} {progress_bar:<{PROGRESS_BAR_LEN}} |', end='', flush=True)

		# Wait
		time.sleep(0.5)

def compress_videos(videos: list[dir_item], target_bitrate: int, output_path: str):

	# Set up temp file for progress monitoring
	temp_file = os.path.join(tempfile.gettempdir(), 'ffmpeg_progress.log')

	# In case something prevented the file from being deleted during previous run
	if os.path.exists(temp_file):
		os.remove(temp_file)

	# Loop trough all videos and compress them to target bitrate
	video_count = len(videos)
	for video in videos:
		video_probe = ffmpeg.probe(video.path)
		total_frames = int(video_probe['streams'][0]['nb_frames'])

		# Rename and get the new full output path
		name, extension = video.name.split('.')
		output_name = name+ 'c.' + extension
		full_output_path = os.path.join(output_path, output_name)

		text_base = f'{videos.index(video)+1}/{video_count} | {video.name} |'

		# Start thread for progress bar
		thread = threading.Thread(target=monitor_compression_progress, args=(temp_file, text_base, total_frames))
		thread.start()

		# Start the compression process
		video_input = ffmpeg.input(video.path)
		ffmpeg.output(video_input, full_output_path,
			**{'c:v': 'hevc_nvenc', 'b:v': target_bitrate*1000, 'loglevel': 'quiet', 'progress': temp_file}
		).overwrite_output().run()

		# Stop the thread
		thread.join()

		# Clears the temporary file for next compression
		open(temp_file, 'w').close()

	# Remove the temporary file
	if os.path.exists(temp_file):
		os.remove(temp_file)

class navigator():
	"""The main object that handles path navigation"""
	commands = ['cd', 'add', 'addall', 'remove', 'removeall', 'view', 'bitrate', 'output', 'run', 'quit', 'exit', 'help']
	current_dir = os.getcwd()
	directory_items: list[dir_item] = []
	selected_videos: list[dir_item] = []
	target_bitrate: int = 0
	output_path = ''

	def __init__(self):
		self.get_directory_contents()

	def get_directory_contents(self):
		"""Gathers all relevant info on the directory's files and stores it"""
		relevant_content = filter_relevant_content(self.current_dir)

		self.directory_items = []
		for i in range(len(relevant_content)):
			item = dir_item()
			item.ID = i
			item.name = relevant_content[i]
			item.path = os.path.join(self.current_dir, item.name)
			item.is_file = os.path.isfile(item.path)

			if item.is_file:
				video_format = ffmpeg.probe(item.path)['format']

				item.extension = item.name.split('.')[-1]
				item.size = int(video_format['size'])
				item.duration = float(video_format['duration'])
				item.bitrate = int(video_format['bit_rate']) // 1000
			else:
				item.extension = 'Folder'
			
			self.directory_items.append(item)

		# Fix selected items
		for selected_item in self.selected_videos:
			for i in range(len(self.directory_items)):
				if selected_item.path == self.directory_items[i].path:
					self.directory_items.pop(i)
					self.directory_items.append(selected_item)

		return OK
	
	def show_directory_contents(self):
		"""Shows directory content in a neat way"""

		# Create view
		view = f'ID | {'Filename':^{MAX_FILENAME_LEN}} | Extension |   Size   | Duration |    Bitrate    | Selected |'

		for item in self.directory_items:
			item_view = f'\n{item.ID:<3}| '
			item.name
			name = str(item.name)
			if len(name) > MAX_FILENAME_LEN:
				name = name[:MAX_FILENAME_LEN-3] + '...'

			if item.is_file:
				size = item.size // 1000000
				if size > 1000:
					size = f'{size/1000:.4} GB'
				else:
					size = f'{size} MB'

				duration = f'{int(item.duration // 60)}:{round(item.duration % 60):0>2}'
				bitrate = f'{item.bitrate:,} kbps'
				selected = '✓' if item.is_selected else ''

				item_view += f'{name:<{MAX_FILENAME_LEN}} | {item.extension:<10}| {size:<9}| {duration:<9}| {bitrate:<14}| {selected:^9}|'
			else:
				output = ' <- Output dir' if item.path == self.output_path else ''
				item_view += f'{name:<{MAX_FILENAME_LEN}} | {item.extension:<10}{output}'
			
			view += item_view

		print(f'{view}\n')

	def navigation_menu(self):
		"""Shows the navigation menu and handles commands"""
		self.show_directory_contents()

		answer = input(f'{self.current_dir} >> ').split(' ')
		command, arguments = answer[0], answer[1:]

		if command in self.commands:
			exit_code = getattr(self, command)(arguments)
			if command in ['quit', 'exit']:
				return exit_code, -1
			else:
				return exit_code, 1
		else:
			return ERR_CMD_NOT_FOUND, 1
	
	def cd(self, target):
		"""The main command to change directory. Use it like you would in regular terminal."""
		# Cleanup in case of spaces
		target = clean_argument(target)

		# Absolute paths
		if len(target) > 1:
			if target[1] == ':':
				if os.path.isdir(target):
					if target[-1] != '/':
						target += '/'
					self.current_dir = target.replace('\\', '/')
					return OK
				else:
					return ERR_DIR_NOT_FOUND
		
		# Relative paths
		if target == '.':
			return OK
		elif target == '..':
			self.current_dir = os.path.abspath(os.path.dirname(self.current_dir)).replace('\\', '/')
			return OK
		else:
			dir_attempt = os.path.join(self.current_dir, target)
			if os.path.isdir(dir_attempt):
				self.current_dir = dir_attempt.replace('\\', '/')
				return OK
			else:
				return ERR_DIR_NOT_FOUND
	
	def add(self, ID):
		"""Adds video to selection by ID shown in the directory view."""
		number_ID = int(ID[0])
		for item in self.directory_items:
			if number_ID == item.ID and item.is_file:
				if item in self.selected_videos:
					return ERR_ALREADY_SELECTED
				else:
					item.is_selected = True
					self.selected_videos.append(item)
					return OK
	
	def addall(self, _):
		"""Adds all videos in current folder to selection."""
		for item in self.directory_items:
			if item.is_file:
				if not item in self.selected_videos:
					item.is_selected = True
					self.selected_videos.append(item)
		return OK

	def remove(self, ID):
		"""Removes video from selection by ID."""
		number_ID = int(ID[0])
		item_found = False
		for item in self.selected_videos:
			if number_ID == item.ID:
				if item in self.selected_videos:
					item.is_selected = False
					item_found = True
					self.selected_videos.remove(item)

		if item_found:
			return OK
		else:
			return ERR_NOT_IN_SELECTION

	def removeall(self, _):
		"""removes all videos from selection."""
		for item in self.selected_videos:
			item.is_selected = False
		self.selected_videos = []
		return OK
		
	def view(self, _):
		"""Shows all selected videos."""
		print('The following videos are currently selected:')
		for item in self.selected_videos:
			print(f'{item.name}')
		input(CONTINUE_MESSAGE)
		return OK

	def bitrate(self, target_bitrate):
		"""Sets the target bitrate after compression in kbps or literal['low', 'medium', 'high']"""
		if target_bitrate[0].isdigit():
			self.target_bitrate = int(target_bitrate[0])
			return OK
		elif target_bitrate[0] in ['low', 'medium', 'high']:
			return OK
		else:
			return ERR_INVALID_ARG

	def output(self, output_path):
		"""Sets the output folder."""
		# Cleanup in case of spaces
		output_path = clean_argument(output_path)

		# ID numbers
		if output_path.isdigit():
			number_ID = int(output_path)
			for item in self.directory_items:
				if number_ID == item.ID:
					if item.is_file:
						return ERR_FILE_IS_NOT_FOLDER
					else:
						self.output_path = item.path
						return OK
			return ERR_DIR_NOT_FOUND

		# Absolute paths
		if len(output_path) > 1:
			if output_path[1] == ':':
				if os.path.isdir(output_path):
					if output_path[-1] != '/':
						output_path += '/'
					self.output_path = output_path.replace('\\', '/')
					return OK
				else:
					return ERR_DIR_NOT_FOUND
		
		# Relative paths
		dir_attempt = os.path.join(self.current_dir, output_path).replace('\\', '/')
		if os.path.isdir(dir_attempt):
			self.output_path = dir_attempt
			return OK
		else:
			return ERR_DIR_NOT_FOUND

	def run(self, _):
		"""Starts compressing all videos in selection."""

		# Check if all required values are set.
		if self.selected_videos == []:
			return ERR_NO_VIDEOS_SELECTED
		elif self.target_bitrate == 0:
			return ERR_NO_TARGET_BITRATE
		elif self.output_path == '':
			return ERR_NO_OUTPUT_PATH
		else:

			# Ask For confirmation.
			answered = False
			while not answered:
				os.system('cls')
				print('The following videos are to be compressed:')
				print('------------------------------------------')
				for item in self.selected_videos:
					print(f'{item.name}')
				print('------------------------------------------')
				print(f'Target bitrate: {self.target_bitrate} kbps')
				print(f'Output path: {self.output_path}')
				answer = input('Confirm? (y/n) ').lower()
				if answer in ['y', 'n']:
					answered = True

			# Handle confirmation answer.
			if answer == 'y':
				compress_videos(self.selected_videos, self.target_bitrate, self.output_path)
				video_count = len(self.selected_videos)
				if video_count == 1:
					print(f'Done!\n1 compressed video is stored in \'{self.output_path}\'')
				else:
					print(f'Done!\nAll {len(self.selected_videos)} compressed videos are stored in {self.output_path}')
				input(CONTINUE_MESSAGE)
				return OK
			elif answer == 'n':
				return OK

	def quit(self, _):"""Quits the program."""; return OK
	def exit(self, _):"""Equivalent to quit."""; return OK

	def help(self, _):
		"""Shows this help screen. For more info: https://github.com/Rednax-Code/Batch-Video-Compressor"""
		os.system('cls')
		print('You can use the following commands:\n')
		for cmd in self.commands:
			print(f'{cmd} : {getattr(self, cmd).__doc__}')
		input(CONTINUE_MESSAGE)
		return OK

	def __setattr__(self, name, value):
		super().__setattr__(name, value)
		if name == 'current_dir': # To make sure the directory contents are re-accuired when path is changed
			self.get_directory_contents()

def startup_text():
	"""Shows the startup menu (Currently not in use)"""
	print(f'This program converts video files to a certain bitrate.{CONTINUE_MESSAGE}')
	return OK, 1


if __name__ == '__main__':
	nav = navigator()
	menu = 1
	menus = [startup_text, nav.navigation_menu]
	exit_code = 0
	error_messages = {
		1: 'Command not found.',
		2: 'Could not find the folder specified.',
		3: 'Given argument is invalid.',
		4: 'This video is already selected.',
		5: 'This video is not in selection.',
		6: 'No videos are selected for compression.',
		7: 'Please set a target bitrate using the \'bitrate\' command.',
		8: 'Please set an output path using the \'output\' command.',
		9: 'The \'folder\' you tried to select for output, is a video file, not a folder...',
		1000: 'Something wierd happend, Please contact dev.'
	}
	running = True

	while running:		
		exit_code, menu = menus[menu]()

		# Error Handling
		if exit_code != 0:
			os.system('cls')
			print(f'Error {exit_code}: {error_messages[exit_code]}')
		else:
			os.system('cls')
		if menu == -1:
			running = False