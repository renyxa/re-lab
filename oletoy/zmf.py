# Copyright (C) 2013 David Tardon (dtardon@redhat.com)
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

import struct

from utils import add_iter, add_pgiter, rdata

def read(data, offset, fmt):
	return rdata(data, offset, fmt)[0]

zmf_ids = {
}

def parse_header(page, data, parent):
	pass

def parse_text_styles(page, data, parent):
	pass

def parse_pages(page, data, parent):
	pass

def parse_doc(page, data, parent):
	pass

def zmf3_open(page, data, parent, fname):
	if fname == 'Header':
		parse_header(page, data, parent)
	if fname == 'TextStyles.zmf':
		parse_text_styles(page, data, parent)
	elif fname == 'Callisto_doc.zmf':
		parse_doc(page, data, parent)
	elif fname == 'Callisto_pages.zmf':
		parse_pages(page, data, parent)

def zmf5_open(page, data, parent):
	pass

# vim: set ft=python ts=4 sw=4 noet:
