#! -*- UTF-8 -*-
import os
import re
from optparse import OptionParser # argv parser

# add parser options
parser = OptionParser()
parser.add_option('-m', '--volume', dest='volume', help='mount point')
parser.add_option('-p', '--path', dest='isopath', help='path of iso')

(opts, args) = parser.parse_args()

if opts.isopath != None：
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

part = ''

# add a intervention handle afterwards
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
# Exp. sda(x) [U], mmc(x)p(x) [SSD]
disk = re.sub(r'\d+$', '', part) # [0-9]*
index = part.replace(disk, '')
print(index)

boot = root + '/boot'
boot_iso = root + '/iso'

# equals: mkdir -p boot
if not os.path.exists(boot):
	os.mkdir(boot)
if not os.path.exists(boot):
	os.mkdir(boot_iso)

# Copy ISO

