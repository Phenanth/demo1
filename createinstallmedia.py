#! -*- UTF-8 -*-
import os
import re
from shutil import copyfile
from optparse import OptionParser # argv parser

#### Args Parser ####

# add parser options
parser = OptionParser()
parser.add_option('-m', '--volume', dest='volume', help='mount point')
parser.add_option('-p', '--path', dest='isopath', help='path of iso')

(opts, args) = parser.parse_args()

if opts.isopath != None:
	repo = opts.isopath
else:
	repo = os.get_cwd()
if opts.volume != None:
	# replace / from the end
	root = re.sub(r'/+$', '', opts.isopath)
else:
	pass

# ? reinstall directions
# print(opts.volume, opts.isopath)

#### Get Path ####
part = ""

# Add a intervention handle afterwards
for line in open('/proc/mounts').readlines():
	mnt = line.split()
	if root == mnt[1]:
	# if '/boot' == mnt[1]:
		part = mnt[0]
		break

if part == "":
	print("No such mount point found:", root)
	exit(1)

# Chances are that there other naming rules
# Exp: sda(x) [U], mmc(x)p(x) [SSD]
disk = re.sub(r'\d+$', '', part) # [0-9]*
index = part.replace(disk, '')
# print(index)

boot = root + '/boot'
boot_iso = root + '/iso'

equals: mkdir -vp boot
if not os.path.exists(boot):
	os.mkdir(boot)
if not os.path.exists(boot):
	os.mkdir(boot_iso)

#### Copy ISO ####
# -> Get source paths
# repo: 		source file path
# boot_iso: 	target file path
# iso_fn: 		iso file name

src_list = []
# If repo is a directory
if os.path.isdir(repo):
	names = os.listdir(repo)
	# Get file names
	for name in names:
		if name[len(name)-4:len(name)] == '.exe':
			src_list.append(name)
	if len(src_list) == 0:
		print("No iso files in", repo)
		exit(1)
# If repo is a file name and exists
elif os.path.exists(repo):
	src_list = repo
else:
	print(repo, 'is invalid.')
	exit(1)

# Start copy
iso_list = []

count = 1
for iso in src_list:
	print(count, '/', len(src_list))

	iso_fn = iso
	iso_list.append(iso_fn)

	# If iso file is already in the target file path
	if os.path.exists(boot_iso + iso_fn):
		print(boot_iso + iso_fn, 'already exists.')
	# Otherwise, copy the iso file from source to target file path
	else:
		copyfile(repo + iso_fn, boot_iso + iso_fn)

	count += 1

#### Install grub (Not finished) ####
print("Installing grub to", boot, "for", disk, "...")

grub_cmd_grub2 = "grub2-install"
grub_cmd_grub = "grub-install"

# About shutil.which(): see README.md
grub_cmd = ""
grub_cfg = ""
if shutil.which(grub_cmd_grub2) != None:
	grub_cmd = grub_cmd_grub2
	grub_cfg = boot + "/grub2/grub.cfg"
elif shutil.which(grub_cmd_grub) != None:
	grub_cmd = "grub-install --removable"
	grub_cfg = boot + "/grub/grub.cfg"
else:
	print("No grub installer was found.")
	exit(1)
