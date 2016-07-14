# Copyright (C) 2016 David Tardon (dtardon@redhat.com)
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

# Because the ZMF2 format is quite complex--it has a hierarchical
# structure, but the hierarchical "objects" are freely mixed with other
# data--the "standard" way  of showing the important blocks in the page
# view and details in hexdump view doesn't work well--it requires too
# much code duplication. To avoid that duplication, we use an
# abstraction that allows us to treat the views interchangeably. But it
# changes the customary way to add iterators a bit. Namely:
# 1. To open a new block, call view.add_pgiter. Note that instead of a
#    callback name resolved using zmf2_ids you have to pass a function that
#    parses that block. That will be used immediately to create possible
#    further structure in the page view and with a 'delayed effect' to
#    show the structure in the hexdump view. Note that because of the
#    nesting, a parser in the hexdump view doesn't necessarily process
#    the whole data block, so it is necessary to honor the given offset
#    and size.
# 2. To mark a simple peace of data (an int, string, etc.), use
#    view.add_iter. This will only be shown in the hexdump view.
# 3. To change the label of a block inside its parser function (e.g., to
#	 add an ID, name, etc.), use view.set_label.

import utils

class HdView:
	def __init__(self, hd, iter, context=None):
		self.hd = hd
		self.iter = iter
		self.context = context

	def add_iter(self, name, value, offset, length, vtype):
		utils.add_iter(self.hd, name, value, offset, length, vtype, parent=self.iter)

	def add_pgiter(self, name, parser, data, offset, length):
		pgiter = add_iter(self.hd, name, '', offset, length, '%ds' % length, parent=self.iter)
		view = HdView(self.hd, pgiter, self.context)
		return parser(view, data, offset, length)

	def set_label(self, text):
		if self.iter:
			self.hd.model.set(self.iter, 0, text)

	def set_length(self, length):
		pass

class PageView:
	def __init__(self, page, ftype, iter, context=None, data=None, offset=0):
		self.page = page
		self.ftype = ftype
		self.iter = iter
		self.context = context
		self.data = data
		self.offset = offset

	def add_iter(self, name, value, offset, length, vtype):
		pass

	def add_pgiter(self, name, parser, data, offset, length=None):
		if not length:
			length = len(data) - offset
		pgiter = utils.add_pgiter(self.page, name, self.ftype, (parser, self.context),
				data[offset:offset + length], self.iter)
		view = PageView(self.page, self.ftype, pgiter, self.context, data, offset)
		return parser(view, data, offset, length)

	def set_label(self, text):
		self.page.model.set_value(self.iter, 0, text)

	def set_length(self, length):
		if self.data:
			self.page.model.set_value(self.iter, 3, self.data[self.offset:self.offset + length])

# vim: set ft=python sts=4 sw=4 noet:
