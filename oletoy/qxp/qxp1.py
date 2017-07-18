# Copyright (C) 2017 David Tardon (dtardon@redhat.com)
#
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
#

import traceback
from utils import *
from qxp import *

def add_header(hd, size, data, fmt, version):
    off = 0
    version_map = {0x1c: '???', 0x20: '1.10'}
    (ver, off) = rdata(data, off, fmt('H'))
    add_iter(hd, 'Version', key2txt(ver, version_map), off - 2, 2, fmt('H'))
    (ver, off) = rdata(data, off, fmt('H'))
    add_iter(hd, 'Version', key2txt(ver, version_map), off - 2, 2, fmt('H'))
    return (None, size)

def handle_document(page, data, parent, fmt, version, hdr):
    return ((), ())

# vim: set ft=python sts=4 sw=4 noet:
