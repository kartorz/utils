#! /usr/bin/python

"""  Dump raw meta data of iso9660 file system. """

# Author : LiQiong Lee

import sys
import struct
import os
from ctypes import *

BLOCK_SIZE = 2048
F_ISO = ""
g_pathTable = []
g_priVol = None
g_cmd = None

def usage():
    """ Prompt user how to use   """
    print """
Usage: isodump  [dump what] [op]  [iso file]
       [dump what]
       ---------
       boot         - Dump boot record.
       p-volume     - Dump primary volume.
       pathtable    - Dump path table.
       dir-record [block number] [length] - Dump a raw Format of a Directory Record
       iso://dir  [output]        - Dump a dirctory or file to [output]

       NONE         - Dump all the information, if this argument is null.

isodump xx.iso      - Dump the iso image
isodump pathtable xx.iso  - Dump the path table record.
isodump iso:/     xx.iso  - Dump the root directory of iso image.
isodump iso:/boot/grup.cfg  /tmp/grub.cfg  xx.iso  - Dump the file "grup.cfg" to "/tmp/grub.cfg"
"""
    exit()

class PrimaryVolume(Structure):
    _fields = [("sys_identifier", c_char_p),
               ("vol_identifier", c_char_p),
               ("vol_size",       c_uint),
               ("vol_seq",        c_short),
               ("block_size",     c_short),
               ("pt_size",        c_uint),
               ("pt_L_rd",        c_uint),
               ("fs_ver",         c_ubyte),
               ("root_loc",       c_uint),
               ("root_total",     c_uint)]

class DirRecord(Structure):
    susp_buf = None
    _fields = [("len_dr",       c_ubyte),
               ("len_eattr",    c_ubyte),
               ("loc_extent",   c_uint),
               ("len_data",     c_uint),
               ("dt_year",      c_ubyte),
               ("dt_month",     c_ubyte),
               ("dt_hour",      c_ubyte),
               ("dt_minute",    c_ubyte),
               ("dt_second",    c_ubyte),
               ("dt_offset",    c_ubyte),
               ("f_flag",       c_ubyte),
               ("f_unit_size",  c_ubyte),
               ("gap_size",     c_ubyte),
               ("vol_seq_nr",   c_ushort),
               ("len_fi",       c_ubyte),
               ("f_identifier", c_char_p),
               ("sys_use_star", c_uint)]

               
class PathTabelItem(Structure):
    _fields = [("len_di",c_ubyte),
               ("len_eattr", c_ubyte),
               ("loc_extent", c_uint),
               ("pdir_nr", c_ushort),
               ("f_identifier", c_char_p)]

# Return a directory record reading from File and Directory Descriptors.
def read_dirrecord(desc_buf):
    """ Dump file  dirctory record """ 
    dirRec = DirRecord()

    dirRec.len_dr = struct.unpack("B", desc_buf[0])[0]
    if dirRec.len_dr == 0:
        return None;

    dirRec.len_eattr = struct.unpack("B", desc_buf[1])[0]
    dirRec.loc_extent = struct.unpack("<L", desc_buf[2:6])[0]
    dirRec.len_data = struct.unpack("<L", desc_buf[10:14])[0]
    dirRec.f_flag = struct.unpack("B", desc_buf[25])[0]
    dirRec.f_unit_size = struct.unpack("B", desc_buf[26])[0]
    dirRec.gap_size = struct.unpack("B", desc_buf[27])[0]
    dirRec.vol_seq_nr = struct.unpack("<H", desc_buf[28:30])[0]
    dirRec.len_fi = struct.unpack("B", desc_buf[32])[0]
    if dirRec.len_fi == 1:
        dirRec.f_identifier  = struct.unpack("B", desc_buf[33])[0]
        if dirRec.f_identifier  == 0 or dirRec.f_identifier == 1:
            dirRec.f_identifier += int('0')
    else:
        dirRec.f_identifier = desc_buf[33:33+dirRec.len_fi]

    dirRec.sys_use_star = 34 + dirRec.len_fi -1
    if dirRec.len_fi % 2 == 0:
        dirRec.sys_use_star += 1

    if dirRec.len_dr > dirRec.sys_use_star+4:
        dirRec.susp_buf = desc_buf[dirRec.sys_use_star:dirRec.len_dr]
    return dirRec

# Read dirctory records from 'block_nr' with a length of 'total'
# Return a list containing directory records(DirRecord). 
def read_dirs(block_nr=None, total=None):
    """ Read file dirctory records """
    F_ISO.seek(block_nr*BLOCK_SIZE)
    desc_buf = F_ISO.read((total+BLOCK_SIZE-1)/BLOCK_SIZE * BLOCK_SIZE)

    dirs = []
    while True:
        dirItem = read_dirrecord(desc_buf)
        if dirItem == None:
            break;

        dirs.append(dirItem)
        if desc_buf.__len__() > dirItem.len_dr:
            desc_buf = desc_buf[dirItem.len_dr:]            
        else:
           break;
    return dirs;

# Read pathtable record.
def read_pathtable_L(block_nr, total):
    """ Read path table of L typde """
    global g_pathTable

    if g_pathTable != []:
        return

    F_ISO.seek(block_nr*BLOCK_SIZE)
    ptbuf = F_ISO.read(BLOCK_SIZE * ((total+BLOCK_SIZE-1)/BLOCK_SIZE))
    i = 0
    r_size = 0;
    while True :
        i = i+1
        t = PathTabelItem()
        
        t.len_di = struct.unpack('B', ptbuf[0])[0]
        t.len_eattr = struct.unpack('B', ptbuf[1])[0]
        t.loc_extent = struct.unpack('<L', ptbuf[2:6])[0]
        t.pdir_nr = struct.unpack('<H', ptbuf[6:8])[0]
        t.f_identifier = ptbuf[8:8+t.len_di]

        g_pathTable.append(t);

        if t.len_di % 2 :
            len_pd = 1
        else:
            len_pd = 0

        r_size += 9+t.len_di-1+len_pd;
        if r_size >= total:         
            break;
        ptbuf = ptbuf[9+t.len_di-1+len_pd:]

def read_primary_volume(volume_dsc):
    """ Dump primary volume descriptor """
    global BLOCK_SIZE
    global g_priVol

    g_priVol = PrimaryVolume()
    g_priVol.sys_identifier = volume_dsc[8:40]
    g_priVol.vol_identifier = volume_dsc[40:72]
    g_priVol.vol_size = struct.unpack('<L',volume_dsc[80:84])[0]
    g_priVol.vol_seq = struct.unpack('<H',volume_dsc[124:126])[0]
    g_priVol.block_size = struct.unpack('<H',volume_dsc[128:130])[0]
    g_priVol.pt_size = struct.unpack('<L',volume_dsc[132:136])[0]
    g_priVol.pt_L_rd = struct.unpack('<L',volume_dsc[140:144])[0]
    g_priVol.fs_ver = struct.unpack('B', volume_dsc[881])[0]
    dirRec = read_dirrecord(volume_dsc[156:190])
    g_priVol.root_loc = dirRec.loc_extent
    g_priVol.root_total = dirRec.len_data
    BLOCK_SIZE = g_priVol.block_size

# path format /xx/xx, is a directory or file path.
def dump_file(path, output):
    global g_pathTable

    target_diritem = None
    found = False
    is_file = False

    # /root/abc/ - ['', 'root', 'abc', '']
    # /root/abc  - ['', 'root', 'abc']
    # /          - ['', '']
    dircomps = path.split('/')
    if dircomps[-1] == '':
        dircomps.pop()
    if len(dircomps) == 1:
        target_diritem = g_pathTable[0]
    else:
        # Search path table
        pdir_nr = 1 # root
        i_dircomp = 1
        nr = 0;
        while True:
            found = False
            for item in g_pathTable[nr:]:
                nr = nr + 1 # item number in pathtable
                #print "(%d) --> (%s)"%(nr, item.f_identifier)
                if item.pdir_nr < pdir_nr:
                    #print "%d<%d"%(item.pdir_nr, pdir_nr)
                    continue
                elif item.pdir_nr == pdir_nr:
                    #print "finding.."
                    if not found :
                        if item.f_identifier == dircomps[i_dircomp]:
                            target_diritem = item
                            found = True
                            #print "found (%s-->%d)"%(dircomps[i_dircomp], nr)
                            break
                        else:
                            continue
                else:
                    found = False
                    break
            # for item in g_pathTable

            if found:
                # Last dir compentent was found in pathtable, must be a dirctory.
                if i_dircomp == len(dircomps)-1:
                    is_file = False
                    break
                else: # advacne
                    i_dircomp = i_dircomp + 1
                    found = False
                    pdir_nr = nr;
            else:
                # Last dir compentent can't be found in pathtable, may be  a file path.
                if i_dircomp == len(dircomps)-1:
                    found = True
                    is_file = True
                    break
                else:                    
                    print "can't find " + dircomps[i_dircomp]
                    return

    # After search pathtable  
    if found and target_diritem == None:
        target_diritem = g_pathTable[0] # file within root dir.

    dirs = read_dirs(target_diritem.loc_extent, BLOCK_SIZE)
    if dirs != []:
        # Search/dump dir.
        target_fileitem = None
        len_data = dirs[0].len_data
        loc = target_diritem.loc_extent
        while True:
            for d in dirs:
                if is_file:
                    if dircomps[-1] == d.f_identifier:
                        target_fileitem = d                        
                        break
                else:
                    if d.f_identifier == 0:
                       d.f_identifier = '.'
                    elif d.f_identifier == 1:
                       d.f_identifier = '..'
                    print "    %s"%(d.f_identifier)

            if target_fileitem != None:
                break

            len_data = len_data - BLOCK_SIZE
            if len_data > 0:
                loc = loc + 1 # read next block
                dirs = read_dirs(loc, BLOCK_SIZE)
            else:
                break
        # while True

        if is_file and target_fileitem != None:
            loc = target_fileitem.loc_extent
            F_ISO.seek(BLOCK_SIZE * loc)
            length = target_fileitem.len_data
            #print "file length(%d)"%(length)
            r_size = BLOCK_SIZE
            if output == "":
                output = dircomps[-1]
                print "please specify a output file"
                return
            try:
                f_output = open(output, 'wb')
            except(IOError):
                f_output.close()
                print "can't open(%s) for write"
                return

            while True:
                if length == 0:
                    break 
                elif length <= BLOCK_SIZE:
                    r_size = length
                    length = 0
                else:
                    length = length - BLOCK_SIZE

                buf = F_ISO.read(r_size)
                f_output.write(buf)

            f_output.close()
            print "dump (%s) to (%s)"%(path, output)


def dump_dirrecord(dirs=None):
    """ Dump all the file dirctory records contained in desc_buf """

    print "Dump file/deirectory record"
    print "===========================\n" 

    for f in dirs:
        print "length of directory record:(0x%x), length of extend attribute:(%d), location of recore:(%d)BLOCK->(0x%x), data length(%d) size of file unit:(%d), interleave gap size:(%d), file flag:(0x%x),name length:(%d) identify:(%s)\n" %(f.len_dr, f.len_eattr, f.loc_extent, f.loc_extent*BLOCK_SIZE,f.len_data, f.f_unit_size, f.gap_size, f.f_flag, f.len_fi, f.f_identifier)
        #if f.susp_buf != None:
        #    dump_extension_SUSP(f.susp_buf, f.len_dr-f.sys_use_star)

def dump_pathtable_L():
    """ Dump path table of L typde """
    
    print "Dump path table"
    print "================\n"
    i = 0;
    for t in g_pathTable:
        i = i + 1
        if t.len_di == 1:
            if t.f_identifier in [0, 1]:
                print "is a root directory(%d)" %(is_root)
        print "%d->length of identify:(%d), length of extend attribute:(%d), local:(%d)->(0x%x), parent dir number:(%d), identify:(%s)\n" \
            %(i, t.len_di, t.len_eattr, t.loc_extent, t.loc_extent*BLOCK_SIZE, t.pdir_nr, t.f_identifier)

def dump_extension_SUSP(desc_buf, len_buf):
    entry_buf = desc_buf
    len_entry = 0
    total = 0

    while True:
        total += len_entry
        if len_buf - total < 4:
            break;

        entry_buf = entry_buf[len_entry:]

        sig1 = struct.unpack("B", entry_buf[0])[0]
        sig2 = struct.unpack("B", entry_buf[1])[0]
        len_entry = struct.unpack("B", entry_buf[2])[0]
        ver = struct.unpack("B", entry_buf[3])[0]
        print ""
        print "Got a entry(%c,%c) of SUSP with length:(%d), version:(%d)-->" %(sig1,sig2,len_entry, ver),

        if sig1 == ord('C') and sig2 == ord('E'):
            loc = struct.unpack("<L", entry_buf[4:8])[0]
            offset = struct.unpack("<L", entry_buf[12:16])[0]
            len_area = struct.unpack("<L", entry_buf[20:24])[0]
            # loc_buf read loc
            #dump_extension_SUSP(loc_buf)
            print "-->(%d,%d,%d)" %(loc, offset, len_area)
            continue
        
        if sig1 == ord('P') and sig2 == ord('D'):
            continue
    
        if sig1 == ord('S') and sig2 == ord('P'):
            ck1 = struct.unpack("B", entry_buf[4])[0]
            ck2 = struct.unpack("B", entry_buf[5])[0]
            skip = struct.unpack("B", entry_buf[6])[0]
            print "-->(0x%x==0xBE,0x%x==EF,%d)" %(ck1, ck2, skip)
            continue
    
        if sig1 == ord('S') and sig2 == ord('T'):
            return

        if sig1 == ord('E') and sig2 == ord('R'):
            len_id = struct.unpack("B", entry_buf[4])[0]
            len_des = struct.unpack("B", entry_buf[5])[0]
            len_src = struct.unpack("B", entry_buf[6])[0]
            ext_ver = struct.unpack("B", entry_buf[7])[0]
            print "-->(%d,0x%x,0x%x,%d)" %(len_id,len_des,len_src,ext_ver)
            continue

        if sig1 == ord('E') and sig2 == ord('S'):
            continue
        
        if sig1 == ord('R') and sig2 == ord('R'):
            continue

        if sig1 == ord('P') and sig2 == ord('X'):
            f_mode = struct.unpack("<L", entry_buf[4:8])[0]
            s_link = struct.unpack("<L", entry_buf[12:16])[0]
            uid = struct.unpack("<L", entry_buf[20:24])[0]
            gid = struct.unpack("<L", entry_buf[28:32])[0]
            #f_serial_nr = struct.unpack("<L", entry_buf[36:40])[0]
            print "-->(0x%x,0x%x,0x%x,0x%x)" %(f_mode,s_link, uid,gid)
            continue

        if sig1 == ord('N') and sig2 == ord('M'):
            flag = struct.unpack("B", entry_buf[4])[0]
            print "-->(flag:(0x%x), name:(%s))" %(flag, entry_buf[5:len_entry])
            continue

        print "\n"

def dump_primary_volume():
    """ Dump primary volume descriptor """

    global g_priVol

    if g_priVol == None:
        print "Can't dump, read primary volume first"
        return
    print "===== Dump primary volume descriptor =="

    print "System Identifier:(%s)" %(g_priVol.sys_identifier)
    print "Volume Identifier:(%s)" %g_priVol.vol_identifier
    print "Volume Space size:(0x%x)BLOCKS(2kB)" %g_priVol.vol_size
    print "Volume sequence number:(%d)" %(g_priVol.vol_seq)
    print "logic block size:(0x%x)" %(g_priVol.block_size)
    print "Volume path talbe L's BLOCK number is :(0x%x-->0x%x)" %(g_priVol.pt_L_rd, g_priVol.pt_L_rd*BLOCK_SIZE)
    print "Abstract File Identifier: (%s)" %(volume_dsc[739:776])
    print "Bibliographic File Identifier: (%s)" %(volume_dsc[776:813])
    print "pathtable locate (%d)" %(g_priVol.pt_L_rd)
    print "File Structure Version:(%d)" %(g_priVol.fs_ver)
    print "Root directory is at (%d)block, have(0x%x)bytes" %(g_priVol.root_loc, g_priVol.root_total)
#    dump_dirrecord(None, 23, 1)

def dump_boot_record(volume_dsc):
    """ Dump boot record  """

    print "===== Dump boot record =="
    std_identifier = volume_dsc[1:6]
    print "Standard Identifier:(%s)" %std_identifier

    vol_ver = struct.unpack('B', volume_dsc[6])
    print "Volume descriptor version:(%d)" %vol_ver

    bootsys_identifier = volume_dsc[7:39]
    print "boot system identifier(%s)" %bootsys_identifier

    boot_identifier = volume_dsc[39:71]
    print "boot  identifier(%s)" %boot_identifier

if __name__ == '__main__':
    len_arg = len(sys.argv)
    if len_arg >= 3:
        g_cmd = sys.argv[1]
    elif len_arg == 2:
        if sys.argv[1] in ["help", "--help", "-h"]:
           usage()
        else:
            g_cmd = "none"
    else:
        usage()

    try:
        F_ISO = open(sys.argv[len_arg-1], 'rb')
    except(IOError):
        F_ISO.close()
        usage()

    # read volume descriptor
    desc_nr = 0;
    while True:
        desc_nr = desc_nr + 1;
        F_ISO.seek(BLOCK_SIZE*(15+desc_nr))
        volume_dsc = F_ISO.read(BLOCK_SIZE)
        flag = struct.unpack('B',volume_dsc[0])[0]
        if flag == 0:
            if g_cmd in ["none", "boot"]:
                dump_boot_record(volume_dsc)
            continue

        if flag == 1:
            read_primary_volume(volume_dsc)
            dirs = read_dirs(g_priVol.root_loc, g_priVol.root_total)
            
            if g_cmd in ["none", "p-volume"]:
                dump_primary_volume()          
                dump_dirrecord(dirs)
            if g_cmd in ["none", "pathtable"]:
                read_pathtable_L(g_priVol.pt_L_rd, g_priVol.pt_size)
                dump_pathtable_L()
            continue

        if flag == 255:
            break;
    # while True
    
    if g_cmd == "dir-record":
        if len_arg == 5:
            print "dump dir-record (%s, %s)"%(sys.argv[2], sys.argv[3])
            dirs = read_dirs(int(sys.argv[2]), int(sys.argv[3]))
            dump_dirrecord(dirs)
    elif g_cmd.startswith("iso:"):
        o_path = ""
        if len_arg == 4:
            o_path = sys.argv[2]
        
        read_pathtable_L(g_priVol.pt_L_rd, g_priVol.pt_size)
        path = g_cmd[4:]
        print "dump_file(%s)->(%s)"%(path, o_path)
        dump_file(path, o_path)
        
    F_ISO.close()
    
