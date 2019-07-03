#! -*- UTF-8 -*-
import os
import re
from shutil import copyfile, rmtree
import subprocess
from optparse import OptionParser # argv parser

os_type = platform.system()
if os_type != 'Linux':
	raise Exception(os_type + ' NOT supported!')

dist_serial = {}
for dist in ['RHEL', 'CentOS', 'Fedora', 'OL']:
	dist_serial[dist] = 'redhat'
for dist in ['Ubuntu', 'Debian']:
	dist_serial[dist] = 'debian'

# Get block id
# blkid -s <target> <device>
def blk_tag(tag, dev):
	# Execute cmd using sh
	fd = os.popen('blkid -s {} {}'.format(tag, dev))
	for line in fd:
		kv = line.strip().split('=')
		if len(kv) > 1:
			return kv[1].stripe('"')
	return None

# Return type of os of a iso img
def linux_dist(iso):
	label = blk_tag('LABEL', iso)
	for dist in dist_serial:
		if label.startswith(dist):
			return dist_serial[dist]
	return None


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

boot_dir = root + '/boot'
iso_dir = root + '/iso'

# equals: mkdir -vp boot
# if not os.path.exists(boot):
# 	os.mkdir(boot)
# if not os.path.exists(boot):
# 	os.mkdir(boot_iso)

# Multi-directory:
for d in [boot_dir, iso_dir]:
	if not os.path.exists(d):
		os.mkdir(d)

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
		# if name[len(name)-4:len(name)] == '.exe':
		if name.endswith('.iso'):
			# src_list.append(name)
			if linux_dist(name) != None: # If exists the device
				src_list.append(name)
			else:
				print('"{}" skipped.'.format(name))
	if len(src_list) == 0:
		print("No iso files in", repo)
		exit(1)
# If repo is a file name and exists
elif os.path.exists(repo) and linux_dist(repo) != None:
	src_list = [repo]
else:
	print(repo, 'is invalid.')
	exit(1)

# Start copy
iso_list = []

count = 0
for iso in src_list:
	count += 1
	print(count, '/', len(src_list))

	dest_iso = iso_dir + '/' + os.path.basename(iso)
	iso_list.append(dest_iso)

	# If iso file is already in the target file path
	if os.path.exists(dest_iso):
		print(dest_iso, 'already exists.')
	# Otherwise, copy the iso file from source to target file path
	else:
		copyfile(iso, dest_iso)


#### Install grub ####
print("Installing grub to", boot, "for", disk, "...")

grub_cfg = None

# Judge if the installer exists
for grub in ['grub', 'grub2']:
	grub_cmd = grub + '-install'
	if shutil.which(grub_cmd) != None:
		grub_cfg = boot_dir + '/' + grub + '/grub.cfg'
		break

if grub_cfg == None:
	print("No grub installer found!")
	exit(1)

# blk_id
pttype = blk_tag('PTTYPE', disk)
print("{} partition type: {}".format(disk, pttype))

if pttype == 'gpt':
	grub_cmd += ' --target=x86_64-efi'

	esp = None
	fd = os.popen('parted ' + disk + ' print')
	for line in fd:
		fields = line.strip().split()
		if len(fields) > 0 and fields[0].isdigit() and 'esp' in fields:
			esp = fields[0]
			break
		if esp == None:
			print("ESP Partition not found")
			exit(1)

		# Mount parts in /dev
		# os.listdir() will only list basename
		for part in os.listdir('/dev'):
			part = '/dev/' + part
			if re.match(disk + r'\d+', part): # or + '\d+p\d+'
				subprocess.call('umount ' + part)

		efi_dir = boot_dir + '/efi'
		if not os.path.exists(efi_dir):
			os.mkdir(efi_dir)
		# mount <disk+index> <directory>
		subprocess.call('mount {}{} {}'.format(disk, esp, efi_dir), shell=True)
else:
	grub_cmd += ' --target=i386-pc'

for g in ['grub', 'grub2']:
	grub_dir = boot_dir + '/' + g
	if os.path.exists(grub_dir):
		rmtree(grub_dir)

subprocess.call("{} --removable --boot-directory={} {}".format(grub_cmd, boot_dir, disk), shell=True)

#### Generate config menu ####
print("Generating {} ...".format(grub_cfg))

cf = open(grub_cfg, 'w')

configs = ['GRUB_TIMEOUT=5', 'insmod ext2', 'insmod all_video']
if pttype == 'gpt':
	configs.append('insmod part_gpt')

cf.writelines(configs)

# Generate menu
for iso in iso_list:
	iso_rel = iso.lstrip(root)
	lable = blk_tag('LABEL', iso)

	print("{} ({})".format(label, iso_rel))

	if linux_dist(iso) == 'redhat':
		uuid = blk_tag('UUID', part)
		linux = 'isolinux/vmlinuz repo=hd:UUID={}:{}'.format(uuid, iso_dir.lstrip(root))
		initrd = 'isolinux/initrd.img'
	elif linux_dist(iso) == 'debian':
		linux = 'casper/vmlinuz.efi boot=casper iso-scan/filename=' + iso_rel
		initrd = 'casper/initrd.lz'
	else:
		print('Warning: "{}" skipped.'.format(iso))
		continue

	# Msg
	menuentry = [
		"menuentry 'Install" + label + " {",
		"	set root='hd0,{}'".format(index),
		"	loopback lo {}".format(iso_rel)
		"	linux (lo)/{}".format(linux),
		"	initrd (lo)/{}".format(initrd)
		"}"
	]
	cf.writelines(menuentry)

cf.close()

#### Finish ####
# Umount this, reboot
if pttype == 'gpt':
	subprocess.call('umount {}/efi'.format(boot_dir), shell=True)
