#!/usr/bin/env python

# Copyright (C) 2007-2013,	Valek Filippov (frob@df.ru)
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

import sys
import binascii

import App

import fh,fh12

def dump_rec_content(doc,model,iter,level,file):
    ntype=model.get_value(iter,1)
    if ntype == 0:
        return
    size = model.get_value(iter,2)
    data = model.get_value(iter,3)
    if size==0:
        return
    tmpDoc=App.Page()
    tmpDoc.version=doc.version
    if ntype[0] == "fh":
        if fh.hdp.has_key(ntype[1]):
            fh.hdp[ntype[1]](tmpDoc,data,doc)
    elif ntype[0] == "fh12":
        if fh12.fh12_ids.has_key(ntype[1]):
            fh12.fh12_ids[ntype[1]](tmpDoc,size,data,ntype[1])
    tmpModel=tmpDoc.model
    tmpIter = tmpModel.get_iter_first()
    if tmpIter == None:
        return
    text=' '*level
    text+="%s:"%ntype[1]
    while tmpIter != None:
        text+="%s=\"%s\","%(tmpModel.get_value(tmpIter,0),tmpModel.get_value(tmpIter,1))
        tmpIter = tmpModel.iter_next(tmpIter)
    file.write(text+"\n")
    
def dump_rec(doc,model,iter,level,file):
    prefix=' '*level
    suffix=""
    if model.get_value(iter,2)>2000:
        suffix=binascii.hexlify(model.get_value(iter,3)[0:2000])
        suffix+="...[+%dbytes]"%(model.get_value(iter,2)-2000)
    else:
        suffix=binascii.hexlify(model.get_value(iter,3))
    file.write("%s%s:%s\n"%(prefix,model.get_value(iter,1)[1],suffix))
    if model.get_value(iter,2):
        try:
            dump_rec_content(doc,model,iter,level,file)
        except:
            pass
    for i in range(model.iter_n_children(iter)):
        dump_rec(doc,model,model.iter_nth_child(iter,i),level+1,file)
    
def dump(doc,model,file):
   iter = model.get_iter_first()
   if iter == None:
       print "can not find any iter"
       return
   dump_rec(doc,model,iter,1,file)

def main():
    if len(sys.argv)!=3:
        print "Unexpected Number of arguments."
        print "Syntax: oledump.py inputFile outputFile"
        return
    try:
        fs=open(sys.argv[1],"rb")
    except:
        print "can not open %s"%sys.argv[1]
        return
    buf = fs.read()
    if buf:
        doc=App.Page()
        if doc.fload(buf)==0:
            if doc.type=="FH":
                # fh.py use idle function, so we must called them by hand
                try:
                    doc.appdoc.parse_agd_iter().next()
                except:
                    pass
            model=doc.view.get_model()
            try:
                output=open(sys.argv[2],"w")
            except:
                print "can not open output %s"%sys.argv[2]
                return
            dump(doc,model,output)
            output.close()
        else:
            print "can not read the file"
    else:
        print "can not retrieve the file content"
    fs.close()
    
if __name__ == "__main__":
    main()
