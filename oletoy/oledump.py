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

import argparse
import ole
import pub
import quill
import sys
import binascii

import App

import fh,fh12
import iwa

class MiniAppl:
    def __init__(self):
        self.fontsize = 14

class OleDump(object):
    def __init__(self):
        self.m_showData=True
    
    def dump_rec_content(self,doc,model,iter,level,file):
        ntype=model.get_value(iter,1)
        if ntype == 0:
            return
        size = model.get_value(iter,2)
        data = model.get_value(iter,3)
        if size==0:
            return
        miniPage=MiniAppl()
        tmpDoc=App.Page(miniPage)
        tmpDoc.version=doc.version
        done=False
        if doc.appdoc != None:
            try:
                doc.appdoc.update_view2(tmpDoc,model,iter)
                done=True
            except:
                pass
        if done:
            pass
        elif ntype[0] == "fh":
            if ntype[1] in fh.hdp:
                fh.hdp[ntype[1]](tmpDoc,data,doc)
        elif ntype[0] == "fh12":
            if ntype[1] in fh12.fh12_ids:
                fh12.fh12_ids[ntype[1]](tmpDoc,size,data,ntype[1])
        elif ntype[0] == "iwa":
            if ntype[1] in iwa.iwa_ids:
                iwa.iwa_ids[ntype[1]](tmpDoc, size, data)
        elif ntype[0] == "quill":
            if ntype[1] in quill.sub_ids:
                quill.sub_ids[ntype[1]](tmpDoc, size, data)
        elif ntype[0][0:3] == "pub":
            if doc.appcontentdoc != None:
                if ntype[1] in doc.appcontentdoc.pub98_ids:
                    doc.appcontentdoc.pub98_ids[ntype[1]](tmpDoc,size,data)
        elif ntype[0] == "ole" and ntype[1] == "propset":
            ole.suminfo(tmpDoc,data)
        tmpModel=tmpDoc.model
        tmpIter = tmpModel.get_iter_first()
        if tmpIter == None:
            return
        prefix=' '*level
        prefix+="%s[%s]:"%(ntype[1],model.get_value(iter,0))
        i=0
        text=""
        while tmpIter != None:
            text+="%s=\"%s\","%(tmpModel.get_value(tmpIter,0),tmpModel.get_value(tmpIter,1))
            tmpIter = tmpModel.iter_next(tmpIter)
            if len(text)>80:
                file.write("%s%s%s\n"%(prefix,"" if i==0 else "[_%d]"%i,text))
                i+=1
                text=""
        if len(text):
            file.write("%s%s%s\n"%(prefix,"" if i==0 else "[_%d]"%i,text))

    def dump_rec(self,doc,model,iter,level,file):
        prefix=' '*level
        suffix=""
        if model.get_value(iter,2)>2000:
            suffix=binascii.hexlify(model.get_value(iter,3)[0:2000])
            suffix+="...[+%dbytes]"%(model.get_value(iter,2)-2000)
        elif model.get_value(iter,3):
            suffix=binascii.hexlify(model.get_value(iter,3))
        type=model.get_value(iter,1)[1]
        if self.m_showData:
            for i in range((len(suffix)+199)//200):
                file.write("%s%s:%s%s\n"%(prefix,type,"" if i==0 else "[_x%d]"%i,suffix[i*200:(i+1)*200]))
        if model.get_value(iter,2):
            try:
                self.dump_rec_content(doc,model,iter,level,file)
            except:
                pass
        elif not self.m_showData:
            file.write("%s%s\n"%(prefix,type))
        for i in range(model.iter_n_children(iter)):
            self.dump_rec(doc,model,model.iter_nth_child(iter,i),level+1,file)
            
    def dump(self,doc,model,file):
        iter = model.get_iter_first()
        if iter == None:
            print ("can not find any iter")
            return
        while iter != None:
            self.dump_rec(doc,model,iter,1,file)
            iter = model.iter_next(iter)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--hidehexa', action='store_true')
    parser.add_argument('infile')
    parser.add_argument('outfile')
    args = parser.parse_args()
    try:
        fs=open(args.infile,"rb")
    except:
        print ("can not open %s"%args.infile)
        return
    buf = fs.read()
    if buf:
        myAppl=MiniAppl()
        doc=App.Page(myAppl)
        doc.fname=args.infile
        if doc.fload(buf)==0:
            if doc.type=="FH":
                # fh.py use idle function, so we must called them by hand
                try:
                    doc.appdoc.parse_agd_iter(10000).next()
                except:
                    print ("incomplete parsing")
            model=doc.view.get_model()
            try:
                output=open(args.outfile,"w")
            except:
                print ("can not open output %s"%args.outfile)
                return
            dumper=OleDump()
            dumper.m_showData=not args.hidehexa
            dumper.dump(doc,model,output)
            output.close()
        else:
            print ("can not read the file")
    else:
        print ("can not retrieve the file content")
    fs.close()

if __name__ == "__main__":
    main()
