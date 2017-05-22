# Copyright (C) 2017 David Tardon (dtardon@redhat.com)

# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 or later of the GNU General Public
# License as published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301
# USA

import sys

import qxp

seed = int(sys.argv[1], 16)
inc = int(sys.argv[2], 16)
repeat = int(sys.argv[3])
value = int(sys.argv[4], 16)

for i in range(0, repeat):
	seed = (seed + inc) & 0xffff

print('%x' % qxp.deobfuscate(value, seed))

# vim: set ft=python sts=4 sw=4 noet:
