# Copyright (C) 2015 David Tardon (dtardon@redhat.com)
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

import datetime

from utils import add_iter, add_pgiter, bflag2txt, key2txt, rdata

tc6_records = {
	0x1: ('Integer cell', 'tc6_integer_cell'),
	0x2: ('Float cell', 'tc6_float_cell'),
	0x3: ('Text cell', 'tc6_text_cell'),
	0x4: ('Bool cell', 'tc6_bool_cell'),
	0x6: ('Date cell', 'tc6_date_cell'),
	0x8: ('External ref cell', 'tc6_external_ref_cell'),
	0xa: ('Number formula cell', 'tc6_number_formula_cell'),
	0xb: ('Text formula cell', 'tc6_text_formula_cell'),
	0xc: ('Bool formula cell', 'tc6_bool_formula_cell'),
	0xd: ('Error formula cell', 'tc6_error_formula_cell'),
	0xe: ('Date formula cell', 'tc6_date_formula_cell'),
	0x10: ('Column widths', 'tc6_column_widths'),
	0x11: ('Named range', 'tc6_named_range', True),
	0x12: ('Number format def', 'tc6_number_format_def', True),
	0x13: ('Alignment', 'tc6_alignment'),
	0x15: ('Font', 'tc6_font'),
	0x16: ('Vertical line', 'tc6_vertical_line'),
	0x17: ('Horizontal line', 'tc6_horizontal_line'),
	0x18: ('Table', 'tc6_table', True),
	0x1a: ('Number format', 'tc6_number_format'),
	0x1c: ('Cell lock', 'tc6_cell_lock'),
	0x1d: ('Cell type', 'tc6_cell_type'),
	0x1e: ('Macro', 'tc6_macro'),
	0x20: ('Sheet info', 'tc6_sheet_info'),
	0x23: ('Chart', 'tc6_chart'),
	0xff: ('End', None),
}

# func. names in alphabetical order
# TODO: copy directly from c602
tc6_functions = {
	0x0: 'ABS',
	0xf: 'CHOOSE',
	0x14: 'COS',
	0x33: 'ISFORMULA',
	0x3e: 'MAX',
	0x46: 'PI',
	0x55: 'SIGN',
	0x56: 'SIN',
	0x5c: 'SUM',
	0x68: 'TRIM',
	0x76: '_TEXT',
}

class tc6_parser:
	def __init__(self, page, data, parent):
		self.data = data
		self.page = page
		self.parent = parent

	def parse(self):
		assert len(self.data) > 0x40
		add_pgiter(self.page, 'Header', 'c602', 'tc6_header', self.data[0:0x46], self.parent)
		off = 0x46
		while off + 3 <= len(self.data):
			(rec, off) = rdata(self.data, off, '<B')
			(length, off) = rdata(self.data, off, '<H')
			if rec in tc6_records:
				assert len(tc6_records[rec]) >= 2
				name = tc6_records[rec][0]
				handler = tc6_records[rec][1]
				if len(tc6_records[rec]) > 2:
					(id, dummy) = rdata(self.data, off, '<H')
					name += ' [%d]' % id
			else:
				name = 'Record %x' % rec
				handler = None
			if not handler:
				handler = 'tc6_record'
			reciter = add_pgiter(self.page, name, 'c602', handler, self.data[off - 3:off + length], self.parent)
			if rec == 0x23:
				chart = gc6_parser(self.page, self.data[off:off + length], self.parent)
				chart.parse_chart(3, reciter)
			off += length

class gc6_parser:
	def __init__(self, page, data, parent):
		self.data = data
		self.page = page
		self.parent = parent

	def parse(self):
		add_pgiter(self.page, 'Header', 'c602', 'gc6_header', self.data[0:0x40], self.parent)
		off = 0x40
		add_pgiter(self.page, 'Preamble', 'c602', 'gc6_preamble', self.data[off:off + 9], self.parent)
		off += 9
		self.parse_chart(off, self.parent)

	def parse_chart(self, off, parent):
		add_pgiter(self.page, 'Title', 'c602', 'gc6_title', self.data[off:off + 83], parent)
		off += 83
		add_pgiter(self.page, 'Categories', 'c602', 'gc6_categories', self.data[off:off + 87], parent)
		off += 87
		add_pgiter(self.page, 'Values', 'c602', 'gc6_values', self.data[off:off + 88], parent)
		off += 88
		add_pgiter(self.page, 'Legend', 'c602', 'gc6_legend', self.data[off:off + 87], parent)
		off += 87
		add_pgiter(self.page, '3D', 'c602', 'gc6_3d', self.data[off:off + 3], parent)
		off += 3
		add_pgiter(self.page, 'Something', 'c602', '', self.data[off:off + 6], parent)
		off += 6
		add_pgiter(self.page, 'Print settings', 'c602', 'gc6_print_settings', self.data[off:off + 7], parent)
		off += 7
		add_pgiter(self.page, 'Series', 'c602', 'gc6_series', self.data[off:], parent)

def format_row(number):
	return '%d' % (number + 1)

def format_column(number):
	assert number >= 0
	assert number <= 0xff
	low = number % 26
	high = number / 26
	if high > 0:
		row = chr(0x40 + high)
	else:
		row = ''
	return row + chr(0x40 + low + 1)

def format_datetime(dt):
	d = int(dt)
	t = (dt - d) * 86400
	time_str = ''
	if t > 0:
		hm = int(t / 60)
		second = t - 60 * hm
		hour = int(hm / 60)
		minute = int(hm - 60 * hour)
		time_str = " %d:%d:%f" % (hour, minute, second)
	date = datetime.date.fromordinal(d + 1)
	return "%d-%d-%d%s" % (date.year - 1, date.month, date.day, time_str)

def add_tc6_header(hd, size, data):
	off = 0
	(ident, off) = rdata(data, off, '35s')
	add_iter(hd, 'Identifier', ident, off - 35, 35, '35s')

def add_record(hd, size, data):
	off = 0
	(typ, off) = rdata(data, off, '<B')
	add_iter(hd, 'Record type', typ, off - 1, 1, '<B')
	(length, off) = rdata(data, off, '<H')
	add_iter(hd, 'Record length', length, off - 2, 2, '<H')
	return off

def add_text(hd, size, data, off, name='Text'):
	(length, off) = rdata(data, off, '<B')
	add_iter(hd, '%s length' % name, length, off - 1, 1, '<B')
	(text, off) = rdata(data, off, '%ds' % length)
	add_iter(hd, name, str(text, 'cp852'), off - length, length, '%ds' % length)
	return off

def add_range(hd, size, data, off):
	(left, off) = rdata(data, off, '<B')
	add_iter(hd, 'First column', format_column(left), off - 1, 1, '<B')
	(top, off) = rdata(data, off, '<H')
	add_iter(hd, 'First row', format_row(top), off - 2, 2, '<H')
	(right, off) = rdata(data, off, '<B')
	add_iter(hd, 'Last column', format_column(right), off - 1, 1, '<B')
	(bottom, off) = rdata(data, off, '<H')
	add_iter(hd, 'Last row', format_row(bottom), off - 2, 2, '<H')
	return off

def add_table_ref(hd, size, data, off):
	(table, off) = rdata(data, off, '<H')
	if table == 0xffff:
		table_str = 'this'
	else:
		table_str = str(table)
	add_iter(hd, 'Table', table_str, off - 2, 2, '<H')
	return off

def add_chart_type(hd, size, data, off):
	(typ, off) = rdata(data, off, '<B')
	type_map = {
		# 2D
		0x0: 'column', 0x1: 'column - stacked', 0x2: 'column with overlap', 0x3: 'column - percent stacked', 0x4: 'column with values',
		0x5: 'bar', 0x6: 'bar - stacked', 0x7: 'bar with overlap', 0x8: 'bar - percent stacked', 0x9: 'bar with values',
		0xa: 'area - stacked', 0xb: 'area - percent stacked',
		0xc: 'pie', 0xd: 'pie with values', 0xe: 'pie - percent',
		0xf: 'XY - points only', 0x10: 'XY - points and lines',
		0x11: 'line - lines only', 0x12: 'line - points and lines',
		0x13: 'points', 0x14: 'joined points',
		0x15: 'joined',
		# 3D
		0x16: '3D column', 0x17: '3D column - deep', 0x18: '3D column cylinder - deep', 0x19: '3D column pyramid - deep',
		0x1a: '3D bar', 0x1b: '3D bar - deep', 0x1c: '3D bar cylinder - deep', 0x1d: '3D bar pyramid - deep',
		0x1e: '3D lines',
		0x1f: '3D area',
		0x20: '3D pie', 0x21: '3D pie with values', 0x22: '3D pie - percent',
	}
	add_iter(hd, 'Type', key2txt(typ, type_map), off - 1, 1, '<B')
	(two_d, off) = rdata(data, off, '<B')
	add_iter(hd, 'Selected 2D', key2txt(two_d, type_map), off - 1, 1, '<B')
	(three_d, off) = rdata(data, off, '<B')
	add_iter(hd, 'Selected 3D', key2txt(three_d, type_map), off - 1, 1, '<B')

def add_sheet_info(hd, size, data):
	off = add_record(hd, size, data)
	off += 2
	add_range(hd, size, data, off)

def add_cell(hd, size, data):
	off = add_record(hd, size, data)
	(col, off) = rdata(data, off, '<B')
	add_iter(hd, 'Column', format_column(col), off - 1, 1, '<B')
	(row, off) = rdata(data, off, '<H')
	add_iter(hd, 'Row', format_row(row), off - 2, 2, '<H')
	return (off, col, row)

def add_integer_cell(hd, size, data):
	(off, col, row) = add_cell(hd, size, data)
	(val, off) = rdata(data, off, '<h')
	add_iter(hd, 'Value', val, off - 2, 2, '<h')

def add_float_cell(hd, size, data):
	(off, col, row) = add_cell(hd, size, data)
	(val, off) = rdata(data, off, '<d')
	add_iter(hd, 'Value', val, off - 8, 8, '<d')

def add_text_cell(hd, size, data):
	(off, col, row) = add_cell(hd, size, data)
	add_text(hd, size, data, off)

def add_bool_cell(hd, size, data):
	(off, col, row) = add_cell(hd, size, data)
	(val, off) = rdata(data, off, '<B')
	add_iter(hd, 'Value', bool(val), off - 1, 1, '<B')

def add_date_cell(hd, size, data):
	(off, col, row) = add_cell(hd, size, data)
	(datetime, off) = rdata(data, off, '<d')
	add_iter(hd, 'Date/time', format_datetime(datetime), off - 8, 8, '<d')

def add_formula(hd, size, data, off, col=None, row=None):
	def add_address(off, flags, colname, rowname):
		(acol, off) = rdata(data, off, '<b')
		if flags & 0x1 == 0:
			if col == None:
				acol_str = '%+d' % acol
			else:
				acol_str = format_column(acol + col)
		else:
			acol_str = format_column(acol)
		add_iter(hd, colname, acol_str, off - 1, 1, '<b')
		(arow, off) = rdata(data, off, '<h')
		if flags & 0x2 == 0:
			if row == None:
				arow_str = '%+d' % arow
			else:
				arow_str = format_row(arow + row)
		else:
			arow_str = format_row(arow)
		add_iter(hd, rowname, arow_str, off - 2, 2, '<h')
		return off

	def format_abs(flags):
		res = ''
		if opcode & 0x1:
			res += '$C'
		if opcode & 0x2:
			res += '$R'
		return res

	(length, off) = rdata(data, off, '<H')
	add_iter(hd, 'Bytecode length', length, off - 2, 2, '<H')
	opcode_map = {
		0x0: '=',
		# binary operators
		0x4: '=', 0x5: '<', 0x6: '>', 0x7: '<=', 0x8: '>=', 0x9: '<>', 0xb: '+', 0xc: '-', 0xd: '*', 0xe: '/', 0xf: '^',
		# unary operators
		0x11: '-', 0x13: 'argument list', 0x14: 'string', 0x15: 'double', 0x18: 'function', 0x19: '+', 0x1c: 'integer', 0x1f: 'name',
		# address range
		0x20: 'range',
		# address
		0x30: 'address', 0x34: 'date/time'
	}
	while off < size:
		(opcode, off) = rdata(data, off, '<B')
		if opcode < 0x20 or opcode >= 0x34:
			add_iter(hd, 'Opcode', key2txt(opcode, opcode_map), off - 1, 1, '<B')
		elif opcode & 0xf0 == 0x20:
			first = format_abs(opcode)
			last = format_abs(opcode >> 2)
			arange = ''
			if len(first) != 0 or len(last) != 0:
				arange = ' (%s:%s)' % (first, last)
			add_iter(hd, 'Opcode', 'address range%s' % arange, off - 1, 1, '<B')
		elif opcode & 0xf0 == 0x30:
			addr = format_abs(opcode)
			if len(addr) != 0:
				addr = ' (%s)' % addr
			add_iter(hd, 'Opcode', 'address%s' % addr, off - 1, 1, '<B')

		if opcode == 0x13:
			(argc, off) = rdata(data, off, '<B')
			add_iter(hd, 'Number of arguments', argc, off - 1, 1, '<B')
		elif opcode == 0x14:
			off = add_text(hd, size, data, off, 'String')
		elif opcode == 0x15:
			(val, off) = rdata(data, off, '<d')
			add_iter(hd, 'Value', val, off - 8, 8, '<d')
		elif opcode == 0x18:
			(fname, off) = rdata(data, off, '<H')
			add_iter(hd, 'Function', key2txt(fname, tc6_functions), off - 2, 2, '<H')
		elif opcode == 0x1c:
			(val, off) = rdata(data, off, '<h')
			add_iter(hd, 'Value', val, off - 2, 2, '<h')
		elif opcode == 0x1f:
			off += 2
			(name, off) = rdata(data, off, '<H')
			add_iter(hd, 'Name ID', name, off - 2, 2, '<H')
		elif opcode == 0x34:
			(datetime, off) = rdata(data, off, '<d')
			add_iter(hd, 'Date/time', format_datetime(datetime), off - 8, 8, '<d')
		elif opcode & 0xf0 == 0x20:
			off = add_table_ref(hd, size, data, off)
			off = add_address(off, opcode, 'First column', 'First row')
			off = add_address(off, opcode >> 2, 'Last column', 'Last row')
		elif opcode & 0xf0 == 0x30:
			off = add_table_ref(hd, size, data, off)
			off = add_address(off, opcode & 0xf, 'Column', 'Row')

def add_external_ref_cell(hd, size, data):
	(off, col, row) = add_cell(hd, size, data)
	add_formula(hd, size, data, off, col, row)

def add_number_formula_cell(hd, size, data):
	(off, col, row) = add_cell(hd, size, data)
	(result, off) = rdata(data, off, '<d')
	add_iter(hd, 'Result', result, off - 8, 8, '<d')
	add_formula(hd, size, data, off, col, row)

def add_text_formula_cell(hd, size, data):
	(off, col, row) = add_cell(hd, size, data)
	off = add_text(hd, size, data, off, 'Result')
	add_formula(hd, size, data, off, col, row)

def add_bool_formula_cell(hd, size, data):
	(off, col, row) = add_cell(hd, size, data)
	(result, off) = rdata(data, off, '<B')
	add_iter(hd, 'Result', bool(result), off - 1, 1, '<B')
	add_formula(hd, size, data, off, col, row)

def add_error_formula_cell(hd, size, data):
	(off, col, row) = add_cell(hd, size, data)
	(err, off) = rdata(data, off, '<H')
	add_iter(hd, 'Error', err, off - 2, 2, '<H')
	add_formula(hd, size, data, off, col, row)

def add_date_formula_cell(hd, size, data):
	(off, col, row) = add_cell(hd, size, data)
	(datetime, off) = rdata(data, off, '<d')
	add_iter(hd, 'Date/time', format_datetime(datetime), off - 8, 8, '<d')
	add_formula(hd, size, data, off, col, row)

def add_number_format_def(hd, size, data):
	off = add_record(hd, size, data)
	(id, off) = rdata(data, off, '<H')
	add_iter(hd, 'ID', id, off - 2, 2, '<H')
	add_text(hd, size, data, off, 'Format')

def add_column_widths(hd, size, data):
	off = add_record(hd, size, data)
	col = 0
	while off < size:
		(width, off) = rdata(data, off, '<B')
		add_iter(hd, 'Column %s' % format_column(col), width, off - 1, 1, '<B')
		col += 1

def add_alignment(hd, size, data):
	off = add_record(hd, size, data)
	align_map = {0: 'default', 1: 'left', 2: 'center', 3: 'right', 4: 'fill'}
	(align, off) = rdata(data, off, '<B')
	add_iter(hd, 'Alignment', key2txt(align, align_map), off - 1, 1, '<B')
	off += 2
	add_range(hd, size, data, off)

def add_font(hd, size, data):
	off = add_record(hd, size, data)
	font_map = {0: 'normal', 1: 'italic', 2: 'bold', 3: 'high', 4: 'gray'}
	(font, off) = rdata(data, off, '<B')
	add_iter(hd, 'Font', key2txt(font, font_map), off - 1, 1, '<B')
	off += 2
	add_range(hd, size, data, off)

def add_vertical_line(hd, size, data):
	off = add_record(hd, size, data)
	(on, off) = rdata(data, off, '<B')
	add_iter(hd, 'On', bool(on), off - 1, 1, '<B')
	off += 2
	add_range(hd, size, data, off)

def add_horizontal_line(hd, size, data):
	off = add_record(hd, size, data)
	(on, off) = rdata(data, off, '<B')
	add_iter(hd, 'On', bool(on), off - 1, 1, '<B')
	off += 2
	add_range(hd, size, data, off)

def add_cell_type(hd, size, data):
	off = add_record(hd, size, data)
	type_map = {0: 'default', 1: 'text'}
	(typ, off) = rdata(data, off, '<B')
	add_iter(hd, 'Type', key2txt(typ, type_map), off - 1, 1, '<B')
	off += 2
	add_range(hd, size, data, off)

def add_cell_lock(hd, size, data):
	off = add_record(hd, size, data)
	lock_flags = {1: 'locked', 2: 'hidden'}
	(lock, off) = rdata(data, off, '<B')
	add_iter(hd, 'Type', bflag2txt(lock, lock_flags), off - 1, 1, '<B')
	off += 2
	add_range(hd, size, data, off)

def add_number_format(hd, size, data):
	off = add_record(hd, size, data)
	(format, off) = rdata(data, off, '<B')
	add_iter(hd, 'Format', format, off - 1, 1, '<B')
	off += 2
	add_range(hd, size, data, off)

def add_named_range(hd, size, data):
	off = add_record(hd, size, data)
	(id, off) = rdata(data, off, '<H')
	add_iter(hd, 'ID', id, off - 2, 2, '<H')
	off = add_text(hd, size, data, off, 'Name')
	(ordinal, off) = rdata(data, off, '<H')
	add_iter(hd, 'Ordinal number', ordinal, off - 2, 2, '<H')
	off += 2
	add_formula(hd, size, data, off)

def add_table(hd, size, data):
	off = add_record(hd, size, data)
	(id, off) = rdata(data, off, '<H')
	add_iter(hd, 'ID', id, off - 2, 2, '<H')
	off = add_text(hd, size, data, off, 'Name')
	off = add_text(hd, size, data, off, 'Path')

def add_macro(hd, size, data):
	off = add_record(hd, size, data)
	(id, off) = rdata(data, off, '<H')
	add_iter(hd, 'ID', id, off - 2, 2, '<H')
	off = add_text(hd, size, data, off, 'Name')
	off = add_text(hd, size, data, off, 'Path')

def add_chart(hd, size, data):
	off = add_record(hd, size, data)
	add_chart_type(hd, size, data, off)

def add_gc6_header(hd, size, data):
	off = 0
	(ident, off) = rdata(data, off, '32s')
	add_iter(hd, 'Identifier', ident, off - 32, 32, '32s')

def add_preamble(hd, size, data):
	add_chart_type(hd, size, data, 6)

def add_section(hd, size, data):
	off = 0
	off = add_text(hd, size, data, 0, 'Label')
	if off < 0x51:
		add_iter(hd, 'Junk', '', off, 0x51 - off, '%ds' % (0x51 - off))
	off = 0x51
	font_map = {1: 'Triplex', 2: 'Small', 3: 'Sans Serif'}
	(font, off) = rdata(data, off, '<B')
	add_iter(hd, 'Font', key2txt(font, font_map), off - 1, 1, '<B')
	(border, off) = rdata(data, off, '<B')
	add_iter(hd, 'Border', bool(border), off - 1, 1, '<B')
	return off

def add_title(hd, size, data):
	off = add_section(hd, size, data)

def add_categories(hd, size, data):
	off = add_section(hd, size, data)
	(axis_dir, off) = rdata(data, off, '<B')
	add_iter(hd, 'Reversed axis direction', bool(axis_dir), off - 1, 1, '<B')
	(axis_label, off) = rdata(data, off, '<B')
	add_iter(hd, 'Vertical axis label', bool(axis_label), off - 1, 1, '<B')
	raster_flags = {1: 'fine', 2: 'coarse'}
	(raster, off) = rdata(data, off, '<B')
	add_iter(hd, 'Raster', bflag2txt(raster, raster_flags), off - 1, 1, '<B')

def add_values(hd, size, data):
	off = add_section(hd, size, data)
	(axis_dir, off) = rdata(data, off, '<B')
	add_iter(hd, 'Reversed axis direction', bool(axis_dir), off - 1, 1, '<B')
	(axis_label, off) = rdata(data, off, '<B')
	add_iter(hd, 'Vertical axis label', bool(axis_label), off - 1, 1, '<B')
	raster_flags = {1: 'fine', 2: 'coarse'}
	(raster, off) = rdata(data, off, '<B')
	add_iter(hd, 'Raster', bflag2txt(raster, raster_flags), off - 1, 1, '<B')
	off += 1
	(zero, off) = rdata(data, off, '<B')
	add_iter(hd, 'Start at zero', bool(zero), off - 1, 1, '<B')

def add_legend(hd, size, data):
	off = add_section(hd, size, data)
	(hide, off) = rdata(data, off, '<B')
	add_iter(hd, 'Hide', bool(hide), off - 1, 1, '<B')
	location_map = {1: 'bottom', 2: 'left', 3: 'right'}
	(location, off) = rdata(data, off, '<B')
	add_iter(hd, 'Location', key2txt(location, location_map), off - 1, 1, '<B')
	(rank, off) = rdata(data, off, '<B')
	add_iter(hd, 'Reversed rank of categories', bool(rank), off - 1, 1, '<B')
	(switch, off) = rdata(data, off, '<B')
	add_iter(hd, 'Switch series and categories', bool(switch), off - 1, 1, '<B')

def add_3d(hd, size, data):
	off = 0
	(desc, off) = rdata(data, off, '<B')
	add_iter(hd, 'Double description of values', bool(desc), off - 1, 1, '<B')
	(raster, off) = rdata(data, off, '<B')
	add_iter(hd, 'Series raster', bool(raster), off - 1, 1, '<B')
	depth_map = {0: 'small', 1: 'medium', 2: 'large'}
	(depth, off) = rdata(data, off, '<B')
	add_iter(hd, 'Series depth', key2txt(depth, depth_map), off - 1, 1, '<B')

def add_print_settings(hd, size, data):
	off = 0
	(height, off) = rdata(data, off, '<H')
	add_iter(hd, 'Height', '%d cm' % height, off - 2, 2, '<H')
	(width, off) = rdata(data, off, '<H')
	add_iter(hd, 'Width', '%d cm' % width, off - 2, 2, '<H')
	(rotate, off) = rdata(data, off, '<B')
	add_iter(hd, 'Rotate', bool(rotate), off - 1, 1, '<B')
	(quality, off) = rdata(data, off, '<B')
	add_iter(hd, 'Higher quality', bool(quality), off - 1, 1, '<B')
	(file, off) = rdata(data, off, '<B')
	add_iter(hd, 'Print to file', bool(file), off - 1, 1, '<B')

def add_series(hd, size, data):
	off = 2
	add_range(hd, size, data, off)

c602_ids = {
	'tc6_header': add_tc6_header,
	'tc6_record': add_record,
	'tc6_sheet_info': add_sheet_info,
	'tc6_integer_cell': add_integer_cell,
	'tc6_float_cell': add_float_cell,
	'tc6_text_cell': add_text_cell,
	'tc6_bool_cell': add_bool_cell,
	'tc6_date_cell': add_date_cell,
	'tc6_external_ref_cell': add_external_ref_cell,
	'tc6_number_formula_cell': add_number_formula_cell,
	'tc6_text_formula_cell': add_text_formula_cell,
	'tc6_bool_formula_cell': add_bool_formula_cell,
	'tc6_error_formula_cell': add_error_formula_cell,
	'tc6_date_formula_cell': add_date_formula_cell,
	'tc6_number_format_def': add_number_format_def,
	'tc6_column_widths': add_column_widths,
	'tc6_alignment': add_alignment,
	'tc6_font': add_font,
	'tc6_vertical_line': add_vertical_line,
	'tc6_horizontal_line': add_horizontal_line,
	'tc6_cell_type': add_cell_type,
	'tc6_cell_lock': add_cell_lock,
	'tc6_number_format': add_number_format,
	'tc6_named_range': add_named_range,
	'tc6_table': add_table,
	'tc6_macro': add_macro,
	'tc6_chart': add_chart,
	'gc6_header': add_gc6_header,
	'gc6_preamble': add_preamble,
	'gc6_title': add_title,
	'gc6_categories': add_categories,
	'gc6_values': add_values,
	'gc6_legend': add_legend,
	'gc6_3d': add_3d,
	'gc6_print_settings': add_print_settings,
	'gc6_series': add_series,
}

def parse_spreadsheet(data, page, parent):
	parser = tc6_parser(page, data, parent)
	parser.parse()

def parse_chart(data, page, parent):
	parser = gc6_parser(page, data, parent)
	parser.parse()

# vim: set ft=python ts=4 sw=4 noet:
