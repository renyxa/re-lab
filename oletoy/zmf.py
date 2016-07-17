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

import zlib

import bmi
import utils
from uniview import HdView, PageView
from utils import add_iter, add_pgiter, rdata, key2txt, d2hex, d2bin, bflag2txt, ms_charsets

def ref2txt(value):
	if value == 0xffffffff:
		return 'none'
	else:
		return '0x%x' % value

def index2txt(value):
	if value == 0:
		return 'none'
	else:
		return value

def merge(first, second):
	d = first.copy()
	d.update(second)
	return d

def update_pgiter_type(page, ftype, stype, iter1):
	page.model.set_value(iter1, 1, (ftype, stype))

fill_types = {
	1: 'Solid',
	2: 'Linear',
	3: 'Radial',
	4: 'Conical',
	5: 'Cross-shaped',
	6: 'Rectangular',
	7: 'Flexible',
	8: 'Bitmap',
}

rectangle_corner_types = {
	1: 'Normal',
	2: 'Round',
	3: 'Round In',
	4: 'Cut'
}

zmf2_objects = {
	# gap
	0x3: 'Page',
	0x4: 'Layer',
	# gap
	0x8: 'Rectangle',
	0x9: 'Image',
	0xa: 'Color',
	# gap
	0xc: 'Fill',
	# gap
	0xe: 'Line',
	# gap
	0x10: 'Ellipse',
	0x11: 'Star',
	0x12: 'Polygon',
	0x13: 'Text frame',
	0x14: 'Table',
	# gap
	0x16: 'Pen',
	# gap
	0x18: 'Shadow',
	# gap
	0x1a: 'Text style def',
	0x1b: 'Artistic text',
	# gap
	0x1e: 'Group',
	0x1f: 'Combined group',
	0x20: 'Blend',
	0x21: 'Blend def?',
	# gap
	0x100: 'Color palette',
	# gap
	0x201: 'Bitmap definition',
	0x202: 'Text style',
}

# defined later
zmf2_handlers = {}

# Show a string where the trailing 0 is included in length
def _add_zmf2_string0(view, data, offset, size, name):
	(length, off) = rdata(data, offset, '<I')
	view.add_iter('%s length' % name, length, off - 4, 4, '<I')
	if length > 1:
		(text, off) = rdata(data, off, '%ds' % (length - 1))
		view.add_iter(name, unicode(text, 'cp1250'), off - length + 1, length, '%ds' % length)
	else:
		view.add_iter(name, '', off, 1, '1s')
	return off + 1

# Show a string where the trailing 0 is not included in length
def _add_zmf2_string(view, data, offset, size, name):
	(length, off) = rdata(data, offset, '<I')
	view.add_iter('%s length' % name, length, off - 4, 4, '<I')
	if length > 0:
		(text, off) = rdata(data, off, '%ds' % length)
		view.add_iter(name, unicode(text, 'cp1250'), off - length, length + 1, '%ds' % (length + 1))
	else:
		view.add_iter(name, '', off, 1, '1s')
	return off + 1

def _add_zmf2_bbox(view, data, offset, size):
	(tl_x, off) = rdata(data, offset, '<I')
	view.add_iter('Top left X', tl_x, off - 4, 4, '<I')
	(tl_y, off) = rdata(data, off, '<I')
	view.add_iter('Top left Y', tl_y, off - 4, 4, '<I')
	(tr_x, off) = rdata(data, off, '<I')
	view.add_iter('Top right X', tr_x, off - 4, 4, '<I')
	(tr_y, off) = rdata(data, off, '<I')
	view.add_iter('Top right Y', tr_y, off - 4, 4, '<I')
	(br_x, off) = rdata(data, off, '<I')
	view.add_iter('Bottom right X', br_x, off - 4, 4, '<I')
	(br_y, off) = rdata(data, off, '<I')
	view.add_iter('Bottom right Y', br_y, off - 4, 4, '<I')
	(bl_x, off) = rdata(data, off, '<I')
	view.add_iter('Bottom left X', bl_x, off - 4, 4, '<I')
	(bl_y, off) = rdata(data, off, '<I')
	view.add_iter('Bottom left Y', bl_y, off - 4, 4, '<I')
	return off

def _add_zmf2_polygon(view, data, offset, size):
	(tl_x, off) = rdata(data, offset, '<I')
	view.add_iter('Top left X?', tl_x, off - 4, 4, '<I')
	(tl_y, off) = rdata(data, off, '<I')
	view.add_iter('Top left Y?', tl_y, off - 4, 4, '<I')
	(br_x, off) = rdata(data, off, '<I')
	view.add_iter('Bottom right X?', br_x, off - 4, 4, '<I')
	(br_y, off) = rdata(data, off, '<I')
	view.add_iter('Bottom right Y?', br_y, off - 4, 4, '<I')
	(points, off) = rdata(data, off, '<I')
	view.add_iter('Number of points', points, off - 4, 4, '<I')
	return off

def _add_zmf2_shape(view, data, offset):
	off = _add_zmf2_object(view, data, offset)
	off = _add_zmf2_object(view, data, off)
	off = _add_zmf2_object(view, data, off)
	if view.context.version == 3:
		(transparency, off) = rdata(data, off, '<I')
		view.add_iter('Has transparency', bool(transparency), off - 4, 4, '<I')
		if bool(transparency):
			off = _add_zmf2_object(view, data, off, 'Transparency')
		off += 8
	return off

def _add_zmf2_group_info(view, data, offset):
	(count, off) = rdata(data, offset, '<I')
	view.add_iter('Number of non-group shapes', count, off - 4, 4, '<I')
	off += 8
	(gidx, off) = rdata(data, off, '<I')
	view.add_iter('Group shape index', (gidx + 1), off - 4, 4, '<I')
	(count2, off) = rdata(data, off, '<I')
	view.add_iter('Number of shapes', count2, off - 4, 4, '<I')
	for i in range(1, count2 + 1):
		off += 4
		(sidx, off) = rdata(data, off, '<I')
		view.add_iter('Shape %d index' % i, (sidx + 1), off - 4, 4, '<I')
	return off

def _add_zmf2_object(view, data, offset, objname=None, parser=None):
	(length, off) = rdata(data, offset, '<I')
	def add_obj(view, data, offset, size):
		name = objname
		handler = parser
		off = offset + 4
		view.add_iter('Length', length, off - 4, 4, '<I')
		# TODO: this is highly speculative
		(typ, off) = rdata(data, off, '<I')
		view.add_iter('Type', typ, off - 4, 4, '<I')
		(subtyp, off) = rdata(data, off, '<I')
		view.add_iter('Subtype', subtyp, off - 4, 4, '<I')
		count = 0
		if typ == 4 and subtyp == 3:
			off += 4
			(obj, off) = rdata(data, off, '<I')
			view.add_iter('Object type', key2txt(obj, zmf2_objects), off - 4, 4, '<I')
			off += 4
			if not handler and zmf2_handlers.has_key(int(obj)):
				handler = zmf2_handlers[int(obj)]
			if zmf2_objects.has_key(int(obj)) and not name:
				name = '%s' % zmf2_objects[int(obj)]
		elif typ == 4 and subtyp == 4:
			off += 4
			(count, off) = rdata(data, off, '<I')
			view.add_iter('Number of subobjects', count, off - 4, 4, '<I')
			name = name + 's'
		elif typ == 8 and subtyp == 5:
			off += 4
			(hlen, off) = rdata(data, off, '<I')
			view.add_iter('Length of header', hlen, off - 4, 4, '<I')
			(count, off) = rdata(data, off, '<I')
			view.add_iter('Number of subobjects', count, off - 4, 4, '<I')
			(nlen, off) = rdata(data, off, '<I')
			view.add_iter('Name length?', nlen, off - 4, 4, '<I')
			if nlen > 0:
				(ntext, off) = rdata(data, off, '%ds' % (nlen - 1))
				off += 1
				name = '%s (%s)' % (name, ntext)
				view.add_iter('Name?', ntext, off - nlen, nlen, '%ds' % nlen)
		else:
			print("object of unknown type (%d, %d) at %x" % (typ, subtyp, offset))
		if not name:
			name = 'Unknown object'
		view.set_label(name)
		if handler:
			off = handler(view, data, off, length)
		elif int(count) > 0:
			for i in range(0, count):
				if typ == 4 and subtyp == 4:
					contained_name = '%s %d' % (objname, (i + 1))
				else:
					contained_name = None
				off = _add_zmf2_object(view, data, off, contained_name)
		return offset + size
	view.add_pgiter(objname, add_obj, data, offset, length)
	return offset + length

def add_zmf2_obj_color(view, data, offset, size):
	type_map = {0: 'RGB', 1: 'CMYK'}
	(typ, off) = rdata(data, offset, '<B')
	view.add_iter('Type?', key2txt(typ, type_map), off - 1, 1, '<B')
	(color, off) = rdata(data, off, '3s')
	view.add_iter('Color (RGB)', d2hex(color), off - 3, 3, '3s')
	off += 1
	(rgb, off) = rdata(data, off, '3s')
	view.add_iter('RGB', d2hex(rgb), off - 3, 3, '3s')
	(cmyk, off) = rdata(data, off, '4s')
	view.add_iter('CMYK', d2hex(cmyk), off - 4, 4, '4s')
	off += 1
	return _add_zmf2_string0(view, data, off, size, 'Name')

def add_zmf2_obj_bitmap_def(view, data, offset, size):
	(bid, off) = rdata(data, offset, '<I')
	view.add_iter('ID', bid, off - 4, 4, '<I')
	return off

def add_zmf2_bitmap_db_doc(view, data, offset, size):
	off = 4
	i = 1
	while off < len(data):
		off = _add_zmf2_object(view, data, off, 'Bitmap %d' % i)
		i += 1
	return off

def add_zmf2_view(view, data, offset, size):
	off = offset + 0x18
	s = ''
	start = off
	(c, off) = rdata(data, off, '<B')
	while c != 0 and off < offset + size:
		s += chr(c)
		(c, off) = rdata(data, off, '<B')
	view.add_iter('Name', unicode(s, 'cp1250'), start, 0x20, '32s')
	return start + 0x20

def add_zmf2_views(view, data, offset, size):
	(count, off) = rdata(data, offset, '<I')
	view.add_iter('Number of views', count, off - 4, 4, '<I')
	for i in range(1, count + 1):
		(length, off) = rdata(data, off, '<I')
		view.add_iter('Length of view %d' % i, length, off - 4, 4, '<I')
		view.add_pgiter('View %d' % i, add_zmf2_view, data, off, length)
		off += length

def add_zmf2_doc(view, data, offset, size):
	off = offset + 8
	(count, off) = rdata(data, off, '<I')
	# TODO: This is not true: I've seen files where the number is bigger
	# than the number of shapes; I've also seen files where it's negative.
	view.add_iter('Total number of shapes?', count, off - 4, 4, '<I')
	off += 0x1c
	(lr_margin, off) = rdata(data, off, '<I')
	view.add_iter('Left & right page margin?', lr_margin, off - 4, 4, '<I')
	(tb_margin, off) = rdata(data, off, '<I')
	view.add_iter('Top & bottom page margin?', tb_margin, off - 4, 4, '<I')
	off += 8
	off = _add_zmf2_string0(view, data, off, size, 'Default layer name?')
	(tl_x, off) = rdata(data, off, '<I')
	view.add_iter('Page top left X?', tl_x, off - 4, 4, '<I')
	(tl_y, off) = rdata(data, off, '<I')
	view.add_iter('Page top left Y?', tl_y, off - 4, 4, '<I')
	(br_x, off) = rdata(data, off, '<I')
	if view.context.version == 3:
		off += 0x28
	else:
		off += 4
	off = _add_zmf2_object(view, data, off, 'Default color?')
	dstart = off
	(dlen, off) = rdata(data, off, '<I')
	view.add_iter('Length of dim. data', dlen, off - 4, 4, '<I')
	off += 8
	(cwidth, off) = rdata(data, off, '<I')
	view.add_iter('Canvas width', cwidth, off - 4, 4, '<I')
	(cheight, off) = rdata(data, off, '<I')
	view.add_iter('Canvas height', cheight, off - 4, 4, '<I')
	off += 4
	(tl_x, off) = rdata(data, off, '<I')
	view.add_iter('Page top left X', tl_x, off - 4, 4, '<I')
	(tl_y, off) = rdata(data, off, '<I')
	view.add_iter('Page top left Y', tl_y, off - 4, 4, '<I')
	if view.context.version == 2:
		(br_x, off) = rdata(data, off, '<I')
		view.add_iter('Page bottom right X', br_x, off - 4, 4, '<I')
		(br_y, off) = rdata(data, off, '<I')
		view.add_iter('Page bottom right Y', br_y, off - 4, 4, '<I')
	off += 4 # something
	(length, off) = rdata(data, off, '<I')
	view.add_iter('Length of something', length, off - 4, 4, '<I')
	off += length
	off += 4 # something
	off += 0x10
	off = _add_zmf2_object(view, data, off, 'Color palette')
	off += 0x4c # something
	off = _add_zmf2_object(view, data, off, 'Page')
	if view.context.version == 3:
		views_len = offset + size - off
		view.add_pgiter('Views', add_zmf2_views, data, off, views_len)
		off += views_len
	return off

def add_zmf2_text_styles_doc(view, data, offset, size):
	(count, off) = rdata(data, offset, '<I')
	view.add_iter('Number of styles?', count, off - 4, 4, '<I')
	for i in range(1, count + 1):
		off = _add_zmf2_object(view, data, off, 'Text style def %d' % i)
	return off

def add_zmf2_obj_text_style_def(view, data, offset, size):
	off = _add_zmf2_string0(view, data, offset, size, 'Style name')
	off = _add_zmf2_string0(view, data, off, size, 'Font?')
	(height, off) = rdata(data, off, '<i')
	view.add_iter('Font height', '%dpt' % abs(height), off - 4, 4, '<i')
	off += 12
	(weight, off) = rdata(data, off, '<I')
	view.add_iter('Font weight', weight, off - 4, 4, '<I')
	(italic, off) = rdata(data, off, '<B')
	view.add_iter('Italic?', bool(italic), off - 1, 1, '<B')
	(underline, off) = rdata(data, off, '<B')
	view.add_iter('Underline?', bool(underline), off - 1, 1, '<B')
	(strikethrough, off) = rdata(data, off, '<B')
	view.add_iter('Strikethrough?', bool(strikethrough), off - 1, 1, '<B')
	off += 5
	off = _add_zmf2_string0(view, data, off, size, 'Font?')
	off = _add_zmf2_object(view, data, off, 'Text color?')
	(key, off) = rdata(data, off, '<I')
	view.add_iter('Shortcut key', 'F%d' % (key + 1), off - 4, 4, '<I')
	off += 1
	align_map = {0x10: 'left', 0x20: 'right', 0x40: 'justify', 0x80: 'center'}
	(align, off) = rdata(data, off, '<B')
	view.add_iter('Alignment', key2txt(align, align_map), off - 1, 1, '<B')
	off += 2
	(first, off) = rdata(data, off, '<I')
	view.add_iter('First line margin', first, off - 4, 4, '<I')
	(left, off) = rdata(data, off, '<I')
	view.add_iter('Left margin', left, off - 4, 4, '<I')
	(right, off) = rdata(data, off, '<I')
	view.add_iter('Right margin', right, off - 4, 4, '<I')
	(before, off) = rdata(data, off, '<I')
	view.add_iter('Space before', before, off - 4, 4, '<I')
	(after, off) = rdata(data, off, '<I')
	view.add_iter('Space after', after, off - 4, 4, '<I')
	(spacing, off) = rdata(data, off, '<f')
	view.add_iter('Line spacing', '%.1f%%' % spacing, off - 4, 4, '<f')
	return off

def add_zmf2_obj_text_style(view, data, offset, size):
	(parent, off) = rdata(data, offset, '<I')
	view.add_iter('Parent style?', parent, off - 4, 4, '<I')
	off = _add_zmf2_object(view, data, off)
	return off

def add_zmf2_obj_color_palette(view, data, offset, size):
	off = _add_zmf2_object(view, data, offset, 'Color')
	if off < offset + size:
		off = _add_zmf2_string0(view, data, off, size, 'Palette name?')
	return off

def add_zmf2_obj_ellipse(view, data, offset, size):
	off = _add_zmf2_shape(view, data, offset)
	off = _add_zmf2_bbox(view, data, off, size)
	return off

def add_zmf2_obj_image(view, data, offset, size):
	off = _add_zmf2_shape(view, data, offset)
	off = _add_zmf2_bbox(view, data, off, size)
	(bid, off) = rdata(data, off, '<I')
	view.add_iter('Bitmap ID?', bid, off - 4, 4, '<I')
	return off + 4

def add_zmf2_obj_layer(view, data, offset, size):
	off = _add_zmf2_object(view, data, offset, 'Shape')
	off = _add_zmf2_string0(view, data, off, size, 'Layer name')
	(visible, off) = rdata(data, off, '<I')
	view.add_iter('Visible', bool(visible), off - 4, 4, '<I')
	(locked, off) = rdata(data, off, '<I')
	view.add_iter('Locked', bool(locked), off - 4, 4, '<I')
	(printable, off) = rdata(data, off, '<I')
	view.add_iter('Printable', bool(printable), off - 4, 4, '<I')
	return off

def add_zmf2_obj_page(view, data, offset, size):
	off = _add_zmf2_object(view, data, offset, 'Layer')
	off = _add_zmf2_object(view, data, off, 'Something')
	off += 8
	(length, off) = rdata(data, off, '<I')
	view.add_iter('Length of something', length, off - 4, 4, '<I')
	off += length
	return off

def add_zmf2_obj_polygon(view, data, offset, size):
	off = _add_zmf2_shape(view, data, offset)
	off = _add_zmf2_polygon(view, data, off, size)
	return off

def add_zmf2_obj_line(view, data, offset, size):
	off = _add_zmf2_shape(view, data, offset)
	(count, off) = rdata(data, off, '<I')
	view.add_iter('Number of points', count, off - 4, 4, '<I')
	i = 0
	while i < int(count):
		(x, off) = rdata(data, off, '<I')
		view.add_iter('Point %d X' % (i + 1), x, off - 4, 4, '<I')
		(y, off) = rdata(data, off, '<I')
		view.add_iter('Point %d Y' % (i + 1), y, off - 4, 4, '<I')
		off += 8
		i += 1
	return off

def add_zmf2_obj_rectangle(view, data, offset, size):
	off = _add_zmf2_shape(view, data, offset)
	off = _add_zmf2_bbox(view, data, off, size)
	(corner, off) = rdata(data, off, '<I')
	view.add_iter('Corner type', key2txt(corner, rectangle_corner_types), off - 4, 4, '<I')
	(rounding, off) = rdata(data, off, '<I')
	view.add_iter('Rounding', rounding, off - 4, 4, '<I')
	return off

def add_zmf2_obj_star(view, data, offset, size):
	off = _add_zmf2_shape(view, data, offset)
	off = _add_zmf2_polygon(view, data, off, size)
	(angle, off) = rdata(data, off, '<I')
	view.add_iter('Point angle?', angle, off - 4, 4, '<I')
	return off

def add_zmf2_obj_group(view, data, offset, size):
	off = _add_zmf2_shape(view, data, offset)
	off = _add_zmf2_group_info(view, data, off)
	return off

def add_zmf2_obj_blend(view, data, offset, size):
	off = _add_zmf2_shape(view, data, offset)
	off += 0x38
	off = _add_zmf2_object(view, data, off)
	off = _add_zmf2_object(view, data, off, 'Path')
	return off

def add_zmf2_obj_blend_def(view, data, offset, size):
	off = offset + 4
	off = _add_zmf2_object(view, data, off)
	off += 4
	off = _add_zmf2_object(view, data, off)
	off += 4
	return off

def add_zmf2_obj_pen(view, data, offset, size):
	type_map = {0: 'solid', 1: 'dash', 2: 'long dash', 3: 'dash dot', 4: 'dash dot dot'}
	(typ, off) = rdata(data, offset, '<I')
	view.add_iter('Type', key2txt(typ, type_map), off - 4, 4, '<I')
	(width, off) = rdata(data, off, '<I')
	view.add_iter('Width', width, off - 4, 4, '<I')
	arrow_map = {0: 'none'}
	(start, off) = rdata(data, off, '<I')
	view.add_iter('Start arrow', key2txt(start, arrow_map), off - 4, 4, '<I')
	(end, off) = rdata(data, off, '<I')
	view.add_iter('End arrow', key2txt(end, arrow_map), off - 4, 4, '<I')
	off = _add_zmf2_object(view, data, off)
	return off

def add_zmf2_obj_fill(view, data, offset, size):
	(typ, off) = rdata(data, offset, '<I')
	view.add_iter('Type', key2txt(typ, fill_types), off - 4, 4, '<I')
	(hcenter, off) = rdata(data, off, '<I')
	view.add_iter('Horizontal center', '%d%%' % hcenter, off - 4, 4, '<I')
	(vcenter, off) = rdata(data, off, '<I')
	view.add_iter('Vertical center', '%d%%' % vcenter, off - 4, 4, '<I')
	(angle, off) = rdata(data, off, '<I')
	view.add_iter('Angle', '%sdeg' % angle, off - 4, 4, '<I')
	(steps, off) = rdata(data, off, '<I')
	view.add_iter('Steps', steps, off - 4, 4, '<I')
	off = _add_zmf2_object(view, data, off, 'Solid color')
	if typ > 1 and typ < 8:
		(colors, off) = rdata(data, off, '<I')
		view.add_iter('Number of gradient colors', colors, off - 4, 4, '<I')
		for i in range(1, colors + 1):
			off = _add_zmf2_object(view, data, off, 'Gradient color %d' % i)
			(pos, off) = rdata(data, off, '<I')
			view.add_iter('Position %d' % i, '%d%%' % pos, off - 4, 4, '<I')
	(bid, off) = rdata(data, off, '<I')
	view.add_iter('Bitmap index', index2txt(bid), off - 4, 4, '<I')
	(fractal, off) = rdata(data, off, '<I')
	view.add_iter('Fractal fill', bool(fractal), off - 4, 4, '<I')
	(tiling, off) = rdata(data, off, '<I')
	view.add_iter('Tiling', bool(tiling), off - 4, 4, '<I')
	res_map = {100: 'low', 200: 'middle', 300: 'high'}
	(res_x, off) = rdata(data, off, '<I')
	view.add_iter('Resolution X?', key2txt(res_x, res_map), off - 4, 4, '<I')
	(res_y, off) = rdata(data, off, '<I')
	view.add_iter('Resolution Y?', key2txt(res_y, res_map), off - 4, 4, '<I')
	off += 8
	(tile_x, off) = rdata(data, off, '<I')
	view.add_iter('Tile size X', tile_x, off - 4, 4, '<I')
	(tile_y, off) = rdata(data, off, '<I')
	view.add_iter('Tile size Y', tile_y, off - 4, 4, '<I')
	(prop, off) = rdata(data, off, '<I')
	view.add_iter('Proportional', bool(prop), off - 4, 4, '<I')
	return off

def add_zmf2_obj_shadow(view, data, offset, size):
	unit_map = {0: 'mm', 1: '%'}
	(unit, off) = rdata(data, offset, '<I')
	view.add_iter('Offset unit', key2txt(unit, unit_map), off - 4, 4, '<I')
	type_map = {0: 'none', 1: 'color', 2: 'brightness'}
	(typ, off) = rdata(data, off, '<I')
	view.add_iter('Type', key2txt(typ, type_map), off - 4, 4, '<I')
	(horiz, off) = rdata(data, off, '<I')
	view.add_iter('Horizontal offset', horiz, off - 4, 4, '<I')
	(vert, off) = rdata(data, off, '<I')
	view.add_iter('Vertical offset', vert, off - 4, 4, '<I')
	(brightness, off) = rdata(data, off, '<I')
	view.add_iter('Brightness', '%d%%' % brightness, off - 4, 4, '<I')
	off = _add_zmf2_object(view, data, off)
	return off

def add_zmf2_obj_table(view, data, offset, size):
	off = _add_zmf2_object(view, data, offset)
	off = _add_zmf2_object(view, data, off)
	off = _add_zmf2_object(view, data, off)
	off = _add_zmf2_bbox(view, data, off, size)
	off += 4
	(rows, off) = rdata(data, off, '<I')
	view.add_iter('Number of rows', rows, off - 4, 4, '<I')
	(cols, off) = rdata(data, off, '<I')
	view.add_iter('Number of columns', cols, off - 4, 4, '<I')
	off += 8
	for i in range(int(cols)):
		(width, off) = rdata(data, off, '<I')
		view.add_iter('Width of column %d' % (i + 1), width, off - 4, 4, '<I')
		off += 4
	try:
		for i in range(int(rows)):
			(height, off) = rdata(data, off, '<I')
			view.add_iter('Height of row %d' % (i + 1), height, off - 4, 4, '<I')
			off += 0x2c
			for j in range(int(cols)):
				(length, off) = rdata(data, off, '<I')
				view.add_iter('String length', length, off - 4, 4, '<I')
				fix = 0
				if int(length) > 0:
					(text, off) = rdata(data, off, '%ds' % int(length))
					view.add_iter('Content', text, off - int(length), int(length), '%ds' % int(length))
					off += 0x29
					fix = 0x29
			off -= fix
			off += 5
	except:
		pass
	return off

def add_zmf2_character(view, data, offset, size):
	(c, off) = rdata(data, offset, '1s')
	view.add_iter('Character', unicode(c, 'cp1250'), off - 1, 1, '1s')
	off += 0x1b
	(style, off) = rdata(data, off, '<I')
	view.add_iter('Style index', style, off - 4, 4, '<I')
	return off

def add_zmf2_obj_text_frame(view, data, offset, size):
	off = _add_zmf2_object(view, data, offset)
	off = _add_zmf2_object(view, data, off)
	off = _add_zmf2_object(view, data, off)
	if view.context.version == 3:
		off += 12
	off = _add_zmf2_bbox(view, data, off, size)
	(count, off) = rdata(data, off, '<I')
	view.add_iter('Number of chars', count, off - 4, 4, '<I')
	for i in range(0, count):
		(length, off) = rdata(data, off, '<I')
		view.add_iter('Length of char. data', length, off - 4, 4, '<I')
		view.add_pgiter('Character %d' % (i + 1), add_zmf2_character, data, off, length)
		off += length
	return off

def add_zmf2_obj_art_text(view, data, offset, size):
	off = _add_zmf2_object(view, data, offset)
	off = _add_zmf2_object(view, data, off)
	off = _add_zmf2_object(view, data, off)
	off += 0x38
	if view.context.version == 3:
		off += 0xc
	off = _add_zmf2_string(view, data, off, size, 'Text')
	off = _add_zmf2_object(view, data, off)
	off = _add_zmf2_object(view, data, off)
	off = _add_zmf2_object(view, data, off)
	return off

def _parse_zmf2_file(page, data, parent, parser):
	# TODO: this is probably set of flags
	(typ, off) = rdata(data, 4, '<H')
	if typ == 0x4:
		update_pgiter_type(page, 'zmf2', 'compressed_file', parent)
		off += 10
		content = bytearray()
		while off + 0x14 < len(data):
			(size, off) = rdata(data, off, '<I')
			# assert off + int(size) <= len(data)
			compressed = data[off:off + size]
			off += size
			try:
				content.extend(zlib.decompress(compressed))
			except zlib.error:
				print("decompression failed")
				break
		view = PageView(page, 'zmf2', parent, page)
		view.add_pgiter('Uncompressed', parser, str(content), 0, len(content))
		if off < len(data):
			add_pgiter(page, 'Trailer', 'zmf2', 0, data[off:], parent)
	else:
		update_pgiter_type(page, 'zmf2', 'file', parent)

def parse_zmf2_bitmap_db_doc(page, data, parent):
	_parse_zmf2_file(page, data, parent, add_zmf2_bitmap_db_doc)

def parse_zmf2_text_styles_doc(page, data, parent):
	_parse_zmf2_file(page, data, parent, add_zmf2_text_styles_doc)

def parse_zmf2_doc(page, data, parent):
	_parse_zmf2_file(page, data, parent, add_zmf2_doc)

def parse_zmf2_pages_doc(page, data, parent):
	pass

zmf2_handlers = {
	0x3: add_zmf2_obj_page,
	0x4: add_zmf2_obj_layer,
	0x8: add_zmf2_obj_rectangle,
	0x9: add_zmf2_obj_image,
	0xa: add_zmf2_obj_color,
	0xc: add_zmf2_obj_fill,
	0xe: add_zmf2_obj_line,
	0x10: add_zmf2_obj_ellipse,
	0x11: add_zmf2_obj_star,
	0x12: add_zmf2_obj_polygon,
	0x13: add_zmf2_obj_text_frame,
	0x14: add_zmf2_obj_table,
	0x16: add_zmf2_obj_pen,
	0x18: add_zmf2_obj_shadow,
	0x1a: add_zmf2_obj_text_style_def,
	0x1b: add_zmf2_obj_art_text,
	0x1e: add_zmf2_obj_group,
	0x1f: add_zmf2_obj_group,
	0x20: add_zmf2_obj_blend,
	0x21: add_zmf2_obj_blend_def,
	0x100: add_zmf2_obj_color_palette,
	0x201: add_zmf2_obj_bitmap_def,
	0x202: add_zmf2_obj_text_style,
}

zmf4_objects = {
	# gap
	0xa: "Fill",
	0xb: "Transparency",
	0xc: "Pen",
	0xd: "Shadow",
	0xe: "Bitmap",
	0xf: "Arrow",
	0x10: "Font",
	0x11: "Paragraph",
	0x12: "Text",
	# gap
	0x1e: "Preview bitmap?",
	# gap
	0x21: "Start of page",
	0x22: "Guidelines",
	0x23: "End of page",
	0x24: "Start of layer",
	0x25: "End of layer",
	0x26: "View",
	0x27: "Document settings",
	0x28: "Color palette",
	# gap
	0x32: "Rectangle",
	0x33: "Ellipse",
	0x34: "Polygon / Star",
	# gap
	0x36: "Curve",
	0x37: "Image",
	# gap
	0x3a: "Text frame",
	0x3b: "Table",
	# gap
	0x41: "Start of group",
	0x42: "End of group/blend",
	0x43: "Start of blend",
	# gap
	0x47: "Style", # only appears in style files (.zms)
}

# defined later
zmf4_handlers = {}

shape_ref_types = {1: 'Fill', 2: 'Pen', 3: 'Shadow', 4: 'Transparency',}

zmf4_object_refs = {
	0xa: {0: 'Fill bitmap'},
	0xc: {0: 'Arrow start', 1: 'Arrow end'},
	0x10: {1: 'Fill', 2: 'Pen'}, # fill ID 0x3 - default (black)?
	0x11: {1: 'Font'},
	0x32: shape_ref_types,
	0x33: shape_ref_types,
	0x34: shape_ref_types,
	0x36: shape_ref_types,
	0x37: merge(shape_ref_types, {5: 'Bitmap'}),
	0x3a: merge(shape_ref_types, {6: 'Text'}),
	0x3b: shape_ref_types,
	0x43: shape_ref_types,
}

class ZMF4Parser(object):

	def __init__(self, data, page, parent):
		self.data = data
		self.page = page
		self.parent = parent
		self.preview_offset = 0

	def parse(self):
		content = self.parse_header()
		self.parse_content(content)

	def parse_header(self):
		(offset, off) = rdata(self.data, 0x20, '<I')
		(preview, off) = rdata(self.data, off, '<I')
		if int(preview) != 0:
			self.preview_offset = int(preview) - int(offset)
			assert self.preview_offset == 0x20 # this is what I see in all files
		data = self.data[0:int(offset)]
		add_pgiter(self.page, 'Header', 'zmf4', 'header', data, self.parent)
		return offset

	def parse_content(self, begin):
		data = self.data[begin:]
		content_iter = add_pgiter(self.page, 'Content', 'zmf4', 0, data, self.parent)
		off = 0
		while off + 4 <= len(data):
			off = self._parse_object(data, off, content_iter)

	def parse_object(self, data, start, length, parent, typ, callback):
		self._do_parse_object(data[start:start + length], parent, typ, callback)
		return start + length

	def parse_preview_bitmap(self, data, start, length, parent, typ, callback):
		data_start = start + length
		(bmp_type, off) = rdata(data, data_start, '2s')
		assert bmp_type == 'BM'
		(size, off) = rdata(data, off, '<I')
		assert data_start + size < len(data)
		objiter = self._do_parse_object(data[start:data_start], parent, typ, callback)
		add_pgiter(self.page, 'Bitmap data', 'zmf4', 'preview_bitmap_data', data[data_start:data_start + size], objiter)
		return data_start + size

	def parse_bitmap(self, data, start, length, parent, typ, callback):
		data_start = start + length
		(something, off) = rdata(data, start + 0x20, '<I')
		has_data = bool(something)
		objiter = self._do_parse_object(data[start:data_start], parent, typ, callback)
		if has_data:
			(bmp_type, off) = rdata(data, data_start, '9s')
			assert bmp_type == 'ZonerBMIa'
			size = bmi.get_size(data[data_start:])
			assert data_start + size < len(data)
			bmi.open(data[data_start:data_start + size], self.page, objiter)
			length += size
		return start + length

	def _parse_object(self, data, start, parent):
		(length, off) = rdata(data, start, '<I')
		(typ, off) = rdata(data, off, '<I')
		if start + length <= len(data):
			if zmf4_handlers.has_key(int(typ)):
				(handler, callback) = zmf4_handlers[int(typ)]
				return handler(self, data, start, length, parent, typ, callback)
			else:
				self._do_parse_object(data[start:start + length], parent, typ, 'obj')
				return start + length

	def _do_parse_object(self, data, parent, typ, callback):
		if zmf4_objects.has_key(typ):
			obj = zmf4_objects[typ]
		else:
			obj = 'Unknown object 0x%x' % typ
		obj_str = obj
		if len(data) >= 0x1c:
			(oid, off) = rdata(data, 0x18, '<I')
			if int(oid) != 0xffffffff:
				obj_str = '%s (0x%x)' % (obj, oid)
		return add_pgiter(self.page, obj_str, 'zmf4', callback, data, parent)

zmf4_handlers = {
	0xA: (ZMF4Parser.parse_object, 'obj_fill'),
	0xB: (ZMF4Parser.parse_object, 'obj_fill'),
	0xC: (ZMF4Parser.parse_object, 'obj_pen'),
	0xD: (ZMF4Parser.parse_object, 'obj_shadow'),
	0xe: (ZMF4Parser.parse_bitmap, 'obj_bitmap'),
	0xf: (ZMF4Parser.parse_object, 'obj_arrow'),
	0x10: (ZMF4Parser.parse_object, 'obj_font'),
	0x11: (ZMF4Parser.parse_object, 'obj_paragraph'),
	0x12: (ZMF4Parser.parse_object, 'obj_text'),
	0x1e: (ZMF4Parser.parse_preview_bitmap, 'obj'),
	0x22: (ZMF4Parser.parse_object, 'obj_guidelines'),
	0x24: (ZMF4Parser.parse_object, 'obj_start_layer'),
	0x26: (ZMF4Parser.parse_object, 'view'),
	0x27: (ZMF4Parser.parse_object, 'obj_doc_settings'),
	0x28: (ZMF4Parser.parse_object, 'obj_color_palette'),
	0x32: (ZMF4Parser.parse_object, 'obj_rectangle'),
	0x33: (ZMF4Parser.parse_object, 'obj_ellipse'),
	0x34: (ZMF4Parser.parse_object, 'obj_polygon'),
	0x36: (ZMF4Parser.parse_object, 'obj_curve'),
	0x37: (ZMF4Parser.parse_object, 'obj_image'),
	0x3a: (ZMF4Parser.parse_object, 'obj_text_frame'),
	0x3b: (ZMF4Parser.parse_object, 'obj_table'),
	0x41: (ZMF4Parser.parse_object, 'obj'),
	0x43: (ZMF4Parser.parse_object, 'obj_blend'),
	0x47: (ZMF4Parser.parse_object, 'obj'),
}

def add_zmf2_bitmap_db(hd, size, data):
	(count, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Number of bitmaps?', count, off - 4, 4, '<I')

def add_zmf2_header(hd, size, data):
	(length, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Length?', length, off - 4, 4, '<I')
	off += 6
	(version, off) = rdata(data, off, '<H')
	add_iter(hd, 'Version', version, off - 2, 2, '<H')
	(sig, off) = rdata(data, off, '<I')
	add_iter(hd, 'Signature', '0x%x' % sig, off - 4, 4, '<I')

def add_zmf2_file(hd, size, data):
	(size, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Size', size, off - 4, 4, '<I')
	(typ, off) = rdata(data, off, '<H')
	add_iter(hd, 'Type', typ, off - 2, 2, '<H')

def add_zmf2_compressed_file(hd, size, data):
	add_zmf2_file(hd, size, data)
	off = 0x10
	i = 0
	while off + 0x14 < size:
		(data_size, off) = rdata(data, off, '<I')
		add_iter(hd, 'Size of data block %d' % i, data_size, off - 4, 4, '<I')
		add_iter(hd, 'Data block %d' % i, '', off, data_size, '%ds' % data_size)
		off += data_size
		i += 1

def add_zmf4_preview_bitmap_data(hd, size, data):
	(typ, off) = rdata(data, 0, '2s')
	add_iter(hd, 'Type', typ, off - 2, 2, '2s')
	(size, off) = rdata(data, off, '<I')
	add_iter(hd, 'Size', size, off - 4, 4, '<I')

def add_zmf4_header(hd, size, data):
	off = 8
	(sig, off) = rdata(data, off, '<I')
	add_iter(hd, 'Signature', '0x%x' % sig, off - 4, 4, '<I')
	(version, off) = rdata(data, off, '<I')
	add_iter(hd, 'Version', version, off - 4, 4, '<I')
	off += 12
	(count, off) = rdata(data, off, '<I')
	add_iter(hd, 'Count of objects', count, off - 4, 4, '<I')
	(content, off) = rdata(data, off, '<I')
	add_iter(hd, 'Start of content', content, off - 4, 4, '<I')
	(preview, off) = rdata(data, off, '<I')
	add_iter(hd, 'Start of preview bitmap', preview, off - 4, 4, '<I')
	off += 16
	(size, off) = rdata(data, off, '<I')
	add_iter(hd, 'File size', size, off - 4, 4, '<I')

def _zmf4_obj_header(hd, size, data):
	header_iter = add_iter(hd, 'Header', '', 0, 28, '28s')
	(size, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Size', size, off - 4, 4, '<I', parent=header_iter)
	(typ, off) = rdata(data, off, '<I')
	if zmf4_objects.has_key(typ):
		obj = zmf4_objects[typ]
	else:
		obj = 'Unknown object 0x%x' % typ
	add_iter(hd, 'Type', obj, off - 4, 4, '<I', parent=header_iter)
	(version, off) = rdata(data, off, '<I')
	add_iter(hd, 'Version?', version, off - 4, 4, '<I', parent=header_iter)
	(ref_obj_count, off) = rdata(data, off, '<I')
	add_iter(hd, 'Count of referenced objects', ref_obj_count, off - 4, 4, '<I', parent=header_iter)
	(refs_start, off) = rdata(data, off, '<I')
	add_iter(hd, 'Start of refs list', refs_start, off - 4, 4, '<I', parent=header_iter)
	(ref_types_start, off) = rdata(data, off, '<I')
	add_iter(hd, 'Start of ref types list', ref_types_start, off - 4, 4, '<I', parent=header_iter)
	(oid, off) = rdata(data, off, '<I')
	add_iter(hd, 'ID', ref2txt(oid), off - 4, 4, '<I', parent=header_iter)
	return (off, typ, version, ref_obj_count, refs_start, ref_types_start)

def _zmf4_obj_refs(hd, size, data, ref_obj_count, off_start, off_tag, type_map):
	types = []
	# Determine names
	off = off_tag
	i = 1
	while i <= ref_obj_count:
		(id, off) = rdata(data, off, '<I')
		if id == 0xffffffff:
			typ = 'Unused'
		else:
			typ = key2txt(id, type_map)
		types.append(typ)
		i += 1
	# Show refs and names
	i = 1
	off = off_start
	while i <= ref_obj_count:
		(ref, off) = rdata(data, off, '<I')
		add_iter(hd, '%s ref' % types[i - 1], ref2txt(ref), off - 4, 4, '<I')
		i += 1
	i = 1
	assert off == off_tag
	while i <= ref_obj_count:
		(id, off) = rdata(data, off, '<I')
		add_iter(hd, 'Ref %d type' % i, types[i - 1], off - 4, 4, '<I')
		i += 1

def _zmf4_obj_bbox(hd, size, data, off):
	# width and height may not be correct in some cases
	# for example looks like it's not updated when resizing objects
	(width, off) = rdata(data, off, '<I')
	add_iter(hd, 'Width (original)', width, off - 4, 4, '<I')
	(height, off) = rdata(data, off, '<I')
	add_iter(hd, 'Height (original)', height, off - 4, 4, '<I')
	i = 1
	while i <= 4:
		# points can be in different order depending on how the object was created (mouse cursor movement direction)
		(x, off) = rdata(data, off, '<I')
		add_iter(hd, 'Bounding box corner %d X' % i, x, off - 4, 4, '<I')
		(y, off) = rdata(data, off, '<I')
		add_iter(hd, 'Bounding box corner %d Y' % i, y, off - 4, 4, '<I')
		i += 1
	return off

def _zmf4_curve_type_list(hd, size, data, off, points, name='Point'):
	types = {
		1: 'Line to',
		2: 'Bezier curve point 1',
		3: 'Bezier curve point 2',
		4: 'Bezier curve point 3'
	}
	i = 1
	while i <= points:
		(type, off) = rdata(data, off, '<I')
		if type != 0x64:
			add_iter(hd, '%s %d type' % (name, i + 1), key2txt(type, types), off - 4, 4, '<I')
		i += 1
	return off

def _zmf4_curve_data(hd, size, data, off):
	(path_len, off) = rdata(data, off, '<I')
	add_iter(hd, 'Length of path data', path_len, off - 4, 4, '<I')
	off += 8
	(components, off) = rdata(data, off, '<I')
	add_iter(hd, 'Number of components', components, off - 4, 4, '<I')
	points = 0
	i = 1
	while i <= components:
		off += 8
		(count, off) = rdata(data, off, '<I')
		points += count
		add_iter(hd, 'Number of points of comp. %d' % i, count, off - 4, 4, '<I')
		(closed, off) = rdata(data, off, '<I')
		add_iter(hd, 'Comp. %d closed' % i, bool(closed), off - 4, 4, '<I')
		i += 1
	i = 1
	while i <= points:
		(x, off) = rdata(data, off, '<I')
		add_iter(hd, 'Point %d X' % i, x, off - 4, 4, '<I')
		(y, off) = rdata(data, off, '<I')
		add_iter(hd, 'Point %d Y' % i, y, off - 4, 4, '<I')
		i += 1
	off = _zmf4_curve_type_list(hd, size, data, off, points)
	return off

def add_zmf4_obj(parser=None):
	def add_empty(hd, size, data, off, version):
		pass
	if not parser:
		parser = add_empty
	def add_object(hd, size, data):
		(off, typ, version, count, refs, types) = _zmf4_obj_header(hd, size, data)
		parser(hd, size, data, off, version)
		if zmf4_object_refs.has_key(typ):
			type_map = zmf4_object_refs[typ]
		else:
			type_map = {}
		_zmf4_obj_refs(hd, size, data, count, refs, types, type_map)
	return add_object

def add_zmf4_obj_start_layer(hd, size, data, off, version):
	flags_map = {0x1: 'visible', 0x2: 'lock', 0x4: 'print'}
	(flags, off) = rdata(data, off, '<B')
	add_iter(hd, 'Flags', bflag2txt(flags, flags_map), off - 1, 1, '<B')
	off += 3
	(name_offset, off) = rdata(data, off, '<I')
	add_iter(hd, 'Name offset', name_offset, off - 4, 4, '<I')
	(order, off) = rdata(data, off, '<I')
	add_iter(hd, 'Layer order', order, off - 4, 4, '<I')
	name_length = size - off
	(name, off) = rdata(data, off, '%ds' % name_length)
	add_iter(hd, 'Name', name, off - name_length, name_length, '%ds' % name_length)

def add_zmf4_obj_doc_settings(hd, size, data, off, version):
	(length, off) = rdata(data, off, '<I')
	add_iter(hd, 'Length of data', length, off - 4, 4, '<I')
	flags_map = {
		0x1: 'show margins',
		0x2: 'print margins',
		0x4: 'show prepress marks',
		0x8: 'print prepress marks',
		0x10: 'show guidelines',
		0x20: 'lock guidelines',
		0x40: 'snap to guidelines',
		0x80: 'show master guidelines',
		0x100: 'lock master guidelines',
		0x200: 'snap to master guidelines',
		0x400: 'show master page',
		0x800: 'print master page',
	}
	(flags, off) = rdata(data, off, '<I')
	add_iter(hd, 'Flags', bflag2txt(flags, flags_map), off - 4, 4, '<I')
	marks_flags_map = {
		0x1: 'show fit marks',
		0x2: 'show cut marks',
		0x4: 'show doc info',
		0x8: 'show date&time',
		0x10: 'show ref colors',
		0x20: 'print fit marks',
		0x40: 'print cut marks',
		0x80: 'print doc info',
		0x100: 'print date&time',
		0x200: 'print ref colors',
	}
	(marks_flags, off) = rdata(data, off, '<I')
	add_iter(hd, 'Prepress marks flags', bflag2txt(marks_flags, marks_flags_map), off - 4, 4, '<I')
	off += 0x14
	(color, off) = rdata(data, off, '3s')
	add_iter(hd, 'Page color (RGB)', d2hex(color), off - 3, 3, '3s')
	off += 5
	(width, off) = rdata(data, off, '<I')
	# Note: maximum possible page size is 40305.08 x 28500 mm. Do not ask me why...
	add_iter(hd, 'Page width', width, off - 4, 4, '<I')
	(height, off) = rdata(data, off, '<I')
	add_iter(hd, 'Page height', height, off - 4, 4, '<I')
	# Note: the margins are relative to respective border. That means
	# that right/bottom margins are typically (always?) negative.
	(left_margin, off) = rdata(data, off, '<i')
	add_iter(hd, 'Left page margin', left_margin, off - 4, 4, '<i')
	(top_margin, off) = rdata(data, off, '<i')
	add_iter(hd, 'Top page margin', top_margin, off - 4, 4, '<i')
	(right_margin, off) = rdata(data, off, '<i')
	add_iter(hd, 'Right page margin', right_margin, off - 4, 4, '<i')
	(bottom_margin, off) = rdata(data, off, '<i')
	add_iter(hd, 'Bottom page margin', bottom_margin, off - 4, 4, '<i')
	(origin_x, off) = rdata(data, off, '<i')
	add_iter(hd, 'Origin X', origin_x, off - 4, 4, '<i')
	(origin_y, off) = rdata(data, off, '<i')
	add_iter(hd, 'Origin Y', origin_y, off - 4, 4, '<i')
	off += 0x4
	grid_flags_map = {0x1: 'dots', 0x2: 'lines', 0x4: 'snap', 0x8: 'show',}
	(grid_flags, off) = rdata(data, off, '<B')
	add_iter(hd, 'Grid flags', bflag2txt(grid_flags, grid_flags_map), off - 1, 1, '<B')
	off += 3
	(h_density, off) = rdata(data, off, '<I')
	add_iter(hd, 'Grid h. density', h_density, off - 4, 4, '<I')
	(v_density, off) = rdata(data, off, '<I')
	add_iter(hd, 'Grid v. density', v_density, off - 4, 4, '<I')
	(dot_step, off) = rdata(data, off, '<I')
	add_iter(hd, 'Grid dot step', dot_step, off - 4, 4, '<I')
	(line_step, off) = rdata(data, off, '<I')
	add_iter(hd, 'Grid line step', line_step, off - 4, 4, '<I')
	off += 0xc
	# The page is placed on a much bigger canvas
	# NOTE: it seems that positions are in respect to canvas, not to page.
	(cwidth, off) = rdata(data, off, '<I')
	add_iter(hd, 'Canvas width', cwidth, off - 4, 4, '<I')
	(cheight, off) = rdata(data, off, '<I')
	add_iter(hd, 'Canvas height', cheight, off - 4, 4, '<I')
	(left, off) = rdata(data, off, '<I')
	add_iter(hd, 'Offset of left side of page', left, off - 4, 4, '<I')
	(top, off) = rdata(data, off, '<I')
	add_iter(hd, 'Offset of top side of page', top, off - 4, 4, '<I')
	(right, off) = rdata(data, off, '<I')
	add_iter(hd, 'Offset of right side of page', right, off - 4, 4, '<I')
	(bottom, off) = rdata(data, off, '<I')
	add_iter(hd, 'Offset of bottom side of page', bottom, off - 4, 4, '<I')
	(left_offset, off) = rdata(data, off, '<I')
	add_iter(hd, 'Real offset of left side of page?', left_offset, off - 4, 4, '<I')
	(top_offset, off) = rdata(data, off, '<I')
	add_iter(hd, 'Real offset of top side of page?', top_offset, off - 4, 4, '<I')

def add_zmf4_obj_color_palette(hd, size, data, off, version):
	(data_size, off) = rdata(data, off, '<I')
	add_iter(hd, 'Length of data', data_size, off - 4, 4, '<I')
	(name_offset, off) = rdata(data, off, '<I')
	add_iter(hd, 'Name offset?', name_offset, off - 4, 4, '<I')
	name_length = data_size - name_offset
	(count, off) = rdata(data, off, '<I')
	add_iter(hd, 'Color count', count, off - 4, 4, '<I')
	i = 1
	while i <= count:
		off += 4
		add_iter(hd, 'Color %d' % i, d2hex(data[off:off+4]), off, 4, '4s')
		off += 8
		i += 1
	(name, off) = rdata(data, off, '%ds' % name_length)
	add_iter(hd, 'Name', name, off - name_length, name_length, '%ds' % name_length)

def add_zmf4_obj_fill(hd, size, data, off, version):
	off += 4
	(data_size, off) = rdata(data, off, '<I')
	add_iter(hd, 'Length of data', data_size, off - 4, 4, '<I')
	(type, off) = rdata(data, off, '<I')
	add_iter(hd, 'Fill type', key2txt(type, fill_types), off - 4, 4, '<I')
	if type == 1:
		off = 0x30
		add_iter(hd, 'Color (RGB)', d2hex(data[off:off+3]), off, 3, '3s')
	else:
		(transform, off) = rdata(data, off, '<I')
		add_iter(hd, 'Transform with object', bool(transform), off - 4, 4, '<I')
		(stop_count, off) = rdata(data, off, '<I')
		add_iter(hd, 'Stop count', stop_count, off - 4, 4, '<I')
		if type == 8:
			(width, off) = rdata(data, off, '<I')
			add_iter(hd, 'Width?', width, off - 4, 4, '<I')
			(height, off) = rdata(data, off, '<I')
			add_iter(hd, 'Height?', height, off - 4, 4, '<I')
		elif type != 2:
			off += 4
			(cx, off) = rdata(data, off, '<f')
			add_iter(hd, 'Center x (%)', cx, off - 4, 4, '<f')
			(cy, off) = rdata(data, off, '<f')
			add_iter(hd, 'Center y (%)', cy, off - 4, 4, '<f')
		if type not in {3, 7}:
			off = 0x3c
			(angle, off) = rdata(data, off, '<f')
			add_iter(hd, 'Angle (rad)', angle, off - 4, 4, '<f')
		off = 0x40
		(steps, off) = rdata(data, off, '<I')
		add_iter(hd, 'Steps', steps, off - 4, 4, '<I')
		off = 0x48
		i = 1
		while i <= stop_count:
			add_iter(hd, 'Stop %d color (RGB)' % i, d2hex(data[off:off+3]), off, 3, '3s')
			off += 8
			(pos, off) = rdata(data, off, '<f')
			add_iter(hd, 'Stop %d position' % i, pos, off - 4, 4, '<f')
			off += 4
			i += 1

def add_zmf4_obj_pen(hd, size, data, off, version):
	off += 4
	(data_size, off) = rdata(data, off, '<I')
	add_iter(hd, 'Length of data', data_size, off - 4, 4, '<I')
	(transform, off) = rdata(data, off, '<I')
	add_iter(hd, 'Transform with object', bool(transform), off - 4, 4, '<I')
	corner_types = {0: 'Miter', 1: 'Round', 2: 'Bevel'}
	(corner_type, off) = rdata(data, off, '<I')
	add_iter(hd, 'Line corner type', key2txt(corner_type, corner_types), off - 4, 4, '<I')
	caps_types = {0: 'Butt', 1: 'Flat', 2: 'Round', 3: 'Pointed'}
	(caps_type, off) = rdata(data, off, '<I')
	add_iter(hd, 'Line caps type', key2txt(caps_type, caps_types), off - 4, 4, '<I')
	(miter, off) = rdata(data, off, '<I')
	add_iter(hd, 'Miter limit', miter, off - 4, 4, '<I')
	(width, off) = rdata(data, off, '<I')
	add_iter(hd, 'Pen width', width, off - 4, 4, '<I')
	off = 0x3c
	add_iter(hd, 'Pen color (RGB)', d2hex(data[off:off+3]), off, 3, '3s')
	off = 0x48
	(angle, off) = rdata(data, off, '<f')
	add_iter(hd, 'Caligraphy angle (rad)', angle, off - 4, 4, '<f')
	(stretch, off) = rdata(data, off, '<f')
	add_iter(hd, 'Caligraphy stretch', '%2d%%' % (stretch * 100), off - 4, 4, '<f')
	off = 0x50
	(dashes, off) = rdata(data, off, '6s')
	add_iter(hd, 'Dash pattern (bits)', d2bin(dashes), off - 6, 6, '6s')
	(dist, off) = rdata(data, off, '<H')
	add_iter(hd, 'Dash pattern length', dist, off - 2, 2, '<H')

def add_zmf4_obj_arrow(hd, size, data, off, version):
	off += 8
	_zmf4_curve_data(hd, size, data, off)

def add_zmf4_obj_shadow(hd, size, data, off, version):
	off += 4
	(data_size, off) = rdata(data, off, '<I')
	add_iter(hd, 'Length of data', data_size, off - 4, 4, '<I')
	shadow_types = {
		1: 'Color',
		2: 'Brightness',
		3: 'Soft',
		4: 'Transparent'
	}
	(type, off) = rdata(data, off, '<I')
	add_iter(hd, 'Shadow type', key2txt(type, shadow_types), off - 4, 4, '<I')
	(x, off) = rdata(data, off, '<I')
	add_iter(hd, 'X offset', x, off - 4, 4, '<I')
	(y, off) = rdata(data, off, '<I')
	add_iter(hd, 'Y offset', y, off - 4, 4, '<I')
	(skew, off) = rdata(data, off, '<f')
	add_iter(hd, 'Skew angle (rad)', skew, off - 4, 4, '<f')
	(transp, off) = rdata(data, off, '<f')
	add_iter(hd, 'Transparency/Brightness', transp, off - 4, 4, '<f')
	add_iter(hd, 'Color (RGB)', d2hex(data[off:off+3]), off, 3, '3s')
	off = 0x40
	(transp2, off) = rdata(data, off, '<f')
	add_iter(hd, 'Transparency (for Soft)', transp2, off - 4, 4, '<f')
	(blur, off) = rdata(data, off, '<I')
	add_iter(hd, 'Blur', blur, off - 4, 4, '<I')

def add_zmf4_obj_ellipse(hd, size, data, off, version):
	off = _zmf4_obj_bbox(hd, size, data, off)
	(begin, off) = rdata(data, off, '<f')
	add_iter(hd, 'Beginning (rad)', begin, off - 4, 4, '<f')
	(end, off) = rdata(data, off, '<f')
	add_iter(hd, 'Ending (rad)', end, off - 4, 4, '<f')
	(arc, off) = rdata(data, off, '<I')
	add_iter(hd, 'Arc (== not closed)', bool(arc), off - 4, 4, '<I')

def add_zmf4_obj_polygon(hd, size, data, off, version):
	off = _zmf4_obj_bbox(hd, size, data, off)
	(peaks, off) = rdata(data, off, '<I')
	add_iter(hd, 'Number of peaks', peaks, off - 4, 4, '<I')
	(count, off) = rdata(data, off, '<I')
	add_iter(hd, 'Number of points describing one peak', count, off - 4, 4, '<I')
	off += 8
	i = 1
	while i <= count:
		(x, off) = rdata(data, off, '<f')
		add_iter(hd, 'Point %d X' % i, x, off - 4, 4, '<f')
		(y, off) = rdata(data, off, '<f')
		add_iter(hd, 'Point %d Y' % i, y, off - 4, 4, '<f')
		i += 1
	_zmf4_curve_type_list(hd, size, data, off, count, 'Point')

def add_zmf4_obj_curve(hd, size, data, off, version):
	(garbage, off) = rdata(data, off, '40s')
	add_iter(hd, 'Unused/garbage?', '', off - 40, 40, '40s')
	_zmf4_curve_data(hd, size, data, off)

def add_zmf4_obj_rectangle(hd, size, data, off, version):
	off = _zmf4_obj_bbox(hd, size, data, off)
	(corner_type, off) = rdata(data, off, '<I')
	add_iter(hd, 'Corner type', key2txt(corner_type, rectangle_corner_types), off - 4, 4, '<I')
	(rounding_value, off) = rdata(data, off, '<f')
	add_iter(hd, 'Rounding', '%.0f%% of shorter side\'s length' % (rounding_value * 50), off - 4, 4, '<f')

def add_zmf4_obj_image(hd, size, data, off, version):
	off = _zmf4_obj_bbox(hd, size, data, off)
	placement_types = {0: 'Stretch', 1: 'Fit', 2: 'Crop'}
	if version == 1:
		(placement_type, off) = rdata(data, off, '<I')
		add_iter(hd, 'Placement type', key2txt(placement_type, placement_types), off - 4, 4, '<I')
	else:
		add_iter(hd, 'Placement type', key2txt(0, placement_types), off, 0, '0s')

def add_zmf4_obj_table(hd, size, data, off, version):
	off = _zmf4_obj_bbox(hd, size, data, off)
	(length, off) = rdata(data, off, '<I')
	add_iter(hd, 'Length of table data', length, off - 4, 4, '<I')
	off += 4
	(rows, off) = rdata(data, off, '<I')
	add_iter(hd, 'Number of rows', rows, off - 4, 4, '<I')
	(cols, off) = rdata(data, off, '<I')
	add_iter(hd, 'Number of columns', cols, off - 4, 4, '<I')
	off += 8
	i = 1
	while i <= rows * cols:
		row = (i - 1) / cols + 1
		column = i - (row - 1) * cols
		cell_iter = add_iter(hd, 'Cell %d (row %d, column %d)' % (i, row, column), '', off, 20, '20s')
		off += 4 # related to vertical pos
		(fill, off) = rdata(data, off, '<I')
		add_iter(hd, 'Fill ref', ref2txt(fill), off - 4, 4, '<I', parent=cell_iter)
		(text, off) = rdata(data, off, '<I')
		add_iter(hd, 'Text ref', ref2txt(text), off - 4, 4, '<I', parent=cell_iter)
		(right_pen, off) = rdata(data, off, '<I')
		# pen with ID 0x1 is used in cells, rows and columns when they have no border
		# (0xffffffff aka None probably not used because it would not override column/row pen)
		add_iter(hd, 'Right border pen ref', ref2txt(right_pen), off - 4, 4, '<I', parent=cell_iter)
		(bottom_pen, off) = rdata(data, off, '<I')
		add_iter(hd, 'Bottom border pen ref', ref2txt(bottom_pen), off - 4, 4, '<I', parent=cell_iter)
		i += 1
	i = 1
	while i <= rows:
		row_iter = add_iter(hd, 'Row %d' % i, '', off, 12, '12s')
		off += 4
		(bottom_pen, off) = rdata(data, off, '<I')
		add_iter(hd, 'Left border pen ref', ref2txt(bottom_pen), off - 4, 4, '<I', parent=row_iter)
		(rel_height, off) = rdata(data, off, '<f')
		add_iter(hd, 'Relative height', '%.0f%%' % (100 * rel_height / rows), off - 4, 4, '<f', parent=row_iter)
		i += 1
	i = 1
	while i <= cols:
		col_iter = add_iter(hd, 'Column %d' % i, '', off, 12, '12s')
		off += 4
		(right_pen, off) = rdata(data, off, '<I')
		add_iter(hd, 'Top border pen ref', ref2txt(right_pen), off - 4, 4, '<I', parent=col_iter)
		(rel_width, off) = rdata(data, off, '<f')
		add_iter(hd, 'Relative width', '%.0f%%' % (100 * rel_width / cols), off - 4, 4, '<f', parent=col_iter)
		i += 1

def add_zmf4_obj_font(hd, size, data, off, version):
	off += 4
	fmt_map = {0x1: 'bold', 0x2: 'italic'}
	(fmt, off) = rdata(data, off, '<B')
	add_iter(hd, 'Format', bflag2txt(fmt, fmt_map), off - 1, 1, '<B')
	off += 3
	(font_size, off) = rdata(data, off, '<f')
	add_iter(hd, 'Font size', '%dpt' % font_size, off - 4, 4, '<f')
	(codepage, off) = rdata(data, off, '<I')
	add_iter(hd, 'Code page', key2txt(codepage, ms_charsets), off - 4, 4, '<I')
	font = ''
	font_pos = off
	# Note: it looks like the font name entry might be fixed size: 32 bytes
	(c, off) = rdata(data, off, '<B')
	while c != 0:
		font += chr(c)
		(c, off) = rdata(data, off, '<B')
	add_iter(hd, 'Font name', font, font_pos, off - font_pos, '%ds' % (off - font_pos))

def add_zmf4_obj_paragraph(hd, size, data, off, version):
	off += 4
	align_map = {0: 'left', 1: 'right', 2: 'block', 3: 'center', 4: 'full'}
	(align, off) = rdata(data, off, '<B')
	add_iter(hd, 'Alignment', key2txt(align, align_map), off - 1, 1, '<B')
	off += 3
	(line, off) = rdata(data, off, '<f')
	add_iter(hd, 'Line spacing', '%2d%%' % (line * 100), off - 4, 4, '<f')

def add_zmf4_obj_text(hd, size, data, off, version):
	off += 4
	(data_size, off) = rdata(data, off, '<I')
	add_iter(hd, 'Length of data', data_size, off - 4, 4, '<I')
	off = 0x28
	(para_count, off) = rdata(data, off, '<I')
	add_iter(hd, 'Number of paragraphs', para_count, off - 4, 4, '<I')
	length = 0
	span_count = 0
	off += 4
	i = 1
	while i <= para_count:
		(count, off) = rdata(data, off, '<I')
		add_iter(hd, 'Spans in paragraph %d' % i, count, off - 4, 4, '<I')
		span_count += count
		(pid, off) = rdata(data, off, '<I')
		add_iter(hd, 'Style of paragraph %d' % i, ref2txt(pid), off - 4, 4, '<I')
		off += 4
		i += 1
	i = 1
	while i <= span_count:
		(count, off) = rdata(data, off, '<I')
		add_iter(hd, 'Length of span %d' % i, count, off - 4, 4, '<I')
		length += 2 * count
		off += 4
		(sid, off) = rdata(data, off, '<I')
		add_iter(hd, 'Font of span %d' % i, ref2txt(sid), off - 4, 4, '<I')
		i += 1
	(text, off) = rdata(data, off, '%ds' % length)
	add_iter(hd, 'Text', unicode(text, 'utf-16le'), off - length, length, '%ds' % length)

def add_zmf4_obj_text_frame(hd, size, data, off, version):
	off = _zmf4_obj_bbox(hd, size, data, off)
	# under && middle baseline == over
	# baseline placement available only for top and bottom alignment
	align_flags = {0x10: 'align middle', 0x20: 'align bottom', 0x1: 'under baseline', 0x2: 'baseline in the middle'}
	default_align = 'align top'
	(align, off) = rdata(data, off, '<B')
	align_str = bflag2txt(align, align_flags)
	if (align & 0x10 == 0) and (align & 0x20 == 0):
		align_str += '/' + default_align
		align_str = align_str.strip('/')
	add_iter(hd, 'Alignment', align_str, off - 1, 1, '<B')
	(placement, off) = rdata(data, off, '<B')
	add_iter(hd, 'Placement type on non-level baseline', placement, off - 1, 1, '<B')
	off += 2
	baseline_end = size - 8 * 3
	baseline_length = baseline_end - off
	add_iter(hd, 'Baseline', '', off, baseline_length, '%ds' % baseline_length)
	_zmf4_curve_data(hd, size, data, off)

def add_zmf4_obj_bitmap(hd, size, data, off, version):
	if size > 0x28:
		path = ''
		(c, off) = rdata(data, 0x28, '<B')
		while c != 0:
			path += chr(c)
			(c, off) = rdata(data, off, '<B')
		add_iter(hd, 'Path', path, 0x28, len(path) + 1, '%ds' % len(path))

def add_zmf4_obj_guidelines(hd, size, data, off, version):
	(count, off) = rdata(data, off, '<I')
	add_iter(hd, 'Count', count, off - 4, 4, '<I')
	off += 4
	type_map = {0: 'vertical', 1: 'horizontal', 2: 'vertical page margin', 3: 'horizontal page margin'}
	for i in range(1, count + 1):
		lineiter = add_iter(hd, 'Guideline %d' % i, '', off, 16, '16s')
		(typ, off) = rdata(data, off, '<I')
		add_iter(hd, 'Type', key2txt(typ, type_map), off - 4, 4, '<I', parent=lineiter)
		(pos, off) = rdata(data, off, '<I')
		add_iter(hd, 'Position', pos, off - 4, 4, '<I', parent=lineiter)
		off += 8

def add_zmf4_obj_blend(hd, size, data, off, version):
	start = off
	(length, off) = rdata(data, off, '<I')
	add_iter(hd, 'Length of data', length, off - 4, 4, '<I')
	off += 4
	(colors, off) = rdata(data, off, '<I')
	add_iter(hd, 'Number of colors', colors, off - 4, 4, '<I')
	off += 4
	(steps, off) = rdata(data, off, '<I')
	add_iter(hd, 'Steps', steps, off - 4, 4, '<I')
	(angle, off) = rdata(data, off, '<f')
	add_iter(hd, 'Angle', '%.2frad' % angle, off - 4, 4, '<f')
	i = 1
	while i <= colors:
		off += 4
		(color, off) = rdata(data, off, '3s')
		add_iter(hd, 'Color %d' % i, d2hex(color), off, 3, '3s')
		off += 5
		(position, off) = rdata(data, off, '<f')
		add_iter(hd, 'Position %d' % i, '%.0f%%' % (100 * position), off - 4, 4, '<f')
		i += 1

def add_zmf4_obj_view(hd, size, data, off, version):
	off += 4
	(left, off) = rdata(data, off, '<I')
	add_iter(hd, 'Left', left, off - 4, 4, '<I')
	(top, off) = rdata(data, off, '<I')
	add_iter(hd, 'Top', top, off - 4, 4, '<I')
	(right, off) = rdata(data, off, '<I')
	add_iter(hd, 'Right', right, off - 4, 4, '<I')
	(bottom, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bottom', bottom, off - 4, 4, '<I')
	(page, off) = rdata(data, off, '<I')
	add_iter(hd, 'Page', page, off - 4, 4, '<I')
	start = off
	name = ''
	(c, off) = rdata(data, off, '<H')
	while c != 0 and off < size:
		name += unichr(c)
		(c, off) = rdata(data, off, '<H')
	add_iter(hd, 'Name', name, start, off - start, '%ds' % (off - start))

zmf2_ids = {
	'header': add_zmf2_header,
	'bitmap_db': add_zmf2_bitmap_db,
	'file': add_zmf2_file,
	'compressed_file': add_zmf2_compressed_file,
}

zmf4_ids = {
	'header': add_zmf4_header,
	'obj': add_zmf4_obj(),
	'obj_start_layer': add_zmf4_obj(add_zmf4_obj_start_layer),
	'obj_doc_settings': add_zmf4_obj(add_zmf4_obj_doc_settings),
	'obj_bitmap': add_zmf4_obj(add_zmf4_obj_bitmap),
	'obj_blend': add_zmf4_obj(add_zmf4_obj_blend),
	'obj_color_palette': add_zmf4_obj(add_zmf4_obj_color_palette),
	'obj_fill': add_zmf4_obj(add_zmf4_obj_fill),
	'obj_font': add_zmf4_obj(add_zmf4_obj_font),
	'obj_guidelines': add_zmf4_obj(add_zmf4_obj_guidelines),
	'obj_image': add_zmf4_obj(add_zmf4_obj_image),
	'obj_paragraph': add_zmf4_obj(add_zmf4_obj_paragraph),
	'obj_pen': add_zmf4_obj(add_zmf4_obj_pen),
	'obj_arrow': add_zmf4_obj(add_zmf4_obj_arrow),
	'obj_shadow': add_zmf4_obj(add_zmf4_obj_shadow),
	'obj_ellipse': add_zmf4_obj(add_zmf4_obj_ellipse),
	'obj_polygon': add_zmf4_obj(add_zmf4_obj_polygon),
	'obj_curve': add_zmf4_obj(add_zmf4_obj_curve),
	'obj_rectangle': add_zmf4_obj(add_zmf4_obj_rectangle),
	'obj_table': add_zmf4_obj(add_zmf4_obj_table),
	'obj_text': add_zmf4_obj(add_zmf4_obj_text),
	'obj_text_frame': add_zmf4_obj(add_zmf4_obj_text_frame),
	'obj_view': add_zmf4_obj(add_zmf4_obj_view),
	'preview_bitmap_data': add_zmf4_preview_bitmap_data,
}

def zmf2_open(page, data, parent, fname):
	file_map = {
		'BitmapDB.zmf': parse_zmf2_bitmap_db_doc,
		'TextStyles.zmf': parse_zmf2_text_styles_doc,
		'Callisto_doc.zmf': parse_zmf2_doc,
		'Callisto_pages.zmf': parse_zmf2_pages_doc,
	}
	if fname == 'Header':
		update_pgiter_type(page, 'zmf2', 'header', parent)
		(page.version, off) = rdata(data, 0xa, '<H')
	elif file_map.has_key(fname):
		if data != None:
			file_map[fname](page, data, parent)

def zmf4_open(data, page, parent):
	parser = ZMF4Parser(data, page, parent)
	parser.parse()

# vim: set ft=python sts=4 sw=4 noet:
