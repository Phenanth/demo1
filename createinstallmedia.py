import os
# import sys
from optparse import OptionParser # 参数解析器

# 添加参数解析选项
parser = OptionParser()
parser.add_option('-m', '--volume', dest='volume', help='mount point')
parser.add_option('-p', '--path', dest='isopath', help='path of iso')

(opts, args) = parser.parse_args()

# 他说要干吗？p重装目录？
print(opts.volume, opts.isopath)
