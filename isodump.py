#! /usr/bin/python

"""  Dump raw meta data of iso9660 file system  """

# Author : LiQiong Lee

import sys
import struct
from ctypes import *

BLOCK_SIZE = 2048
F_ISO = ""

def usage():
    """ Prompt user how to use   """
    print """
Usage: isodump [iso file] [block number]

isodump xx.iso         Dump the iso image
"""
    exit()

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
            loc = struct.unpack("L", entry_buf[4:8])[0]
            offset = struct.unpack("L", entry_buf[12:16])[0]
            len_area = struct.unpack("L", entry_buf[20:24])[0]
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
            continue

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
            f_mode = struct.unpack("L", entry_buf[4:8])[0]
            s_link = struct.unpack("L", entry_buf[12:16])[0]
            uid = struct.unpack("L", entry_buf[20:24])[0]
            gid = struct.unpack("L", entry_buf[28:32])[0]
            f_serial_nr = struct.unpack("L", entry_buf[36:40])[0]
            print "-->(0x%x,0x%x,0x%x,0x%x,0x%x)" %(f_mode,s_link, uid,gid,f_serial_nr)
            continue

def dump_filedir_record(desc_buf=None,block_nr=None, total=None):
    """ Dump file  dirctory record """

    class isofile(Structure):
        _fields = [("len_dr",c_ubyte),
                   ("len_eattr", c_ubyte),
                   ("loc_extent", c_uint),
                   ("len_data", c_uint),
                   ("dt_year", c_ubyte),
                   ("dt_month", c_ubyte),
                   ("dt_hour", c_ubyte),
                   ("dt_minute", c_ubyte),
                   ("dt_second", c_ubyte),
                   ("dt_offset", c_ubyte),
                   ("f_flag", c_ubyte),
                   ("f_unit_size", c_ubyte),
                   ("gap_size", c_ubyte),
                   ("vol_seq_nr", c_ushort),
                   ("len_fi", c_ubyte),
                   ("f_identifier", c_char_p)]

    print "Dump file/deirectory record"
    print "===========================\n" 

    if desc_buf == None:
        F_ISO.seek(block_nr*BLOCK_SIZE)
        desc_buf = F_ISO.read((total+BLOCK_SIZE-1)/BLOCK_SIZE * BLOCK_SIZE)

    while True:
        f = isofile()

        f.len_dr = struct.unpack("B", desc_buf[0])[0]

        if f.len_dr == 0:
            return;

        f.len_eattr = struct.unpack("B", desc_buf[1])[0]
        f.loc_extent = struct.unpack("L", desc_buf[2:6])[0]
        f.len_data = struct.unpack("L", desc_buf[10:14])[0]
        f.f_flag = struct.unpack("B", desc_buf[25])[0]
        f.f_unit_size = struct.unpack("B", desc_buf[26])[0]
        f.gap_size = struct.unpack("B", desc_buf[27])[0]
        f.vol_seq_nr = struct.unpack("H", desc_buf[28:30])[0]
        f.len_fi = struct.unpack("B", desc_buf[32])[0]
        if f.len_fi == 1:
            f.f_identifier  = struct.unpack("B", desc_buf[33])[0]
            if f.f_identifier  == 0 or f.f_identifier == 1:
                f.f_identifier += int('0')
        else:
            f.f_identifier = desc_buf[33:33+f.len_fi]

        print "length of directory record:(%d), length of extend attribute:(%d), location of recore:(%d)BLOCK->(0x%x), data length(%d) size of file unit:(%d), interleave gap size:(%d), file flag:(0x%x),name length:(%d) identify:(%s)\n" %(f.len_dr, f.len_eattr, f.loc_extent, f.loc_extent*BLOCK_SIZE,f.len_data, f.f_unit_size, f.gap_size, f.f_flag, f.len_fi, f.f_identifier)

        sys_use_star = 34 + f.len_fi -1
        if f.len_fi % 2 == 0:
            sys_use_star += 1
    
        if f.len_dr > sys_use_star+4:
            dump_extension_SUSP(desc_buf[sys_use_star:f.len_dr], f.len_dr-sys_use_star)

        if desc_buf.__len__() > f.len_dr:
            desc_buf = desc_buf[f.len_dr:]
        else:
           break;
    
    if desc_buf != None:
    	return (f.loc_extent, f.len_data)

def dump_pathtable_L(block_nr, total):
    """ Dump path table of L typde """
    
    print "Dump path table"
    print "================\n"

    class pathtable(Structure):
        _fields = [("len_di",c_ubyte),
                   ("len_eattr", c_ubyte),
                   ("loc_extent", c_uint),
                   ("pdir_nr", c_ushort),
                   ("f_identifier", c_char_p)]

    F_ISO.seek(block_nr*BLOCK_SIZE)
    ptbuf = F_ISO.read(BLOCK_SIZE * ((total+BLOCK_SIZE-1)/BLOCK_SIZE))
    i = 0
    r_size = 0;
    while True :
        i = i+1
        t = pathtable()

        t.len_di = struct.unpack('B', ptbuf[0])[0]
        t.len_eattr = struct.unpack('B', ptbuf[1])[0]
        t.loc_extent = struct.unpack('L', ptbuf[2:6])[0]
        t.pdir_nr = struct.unpack('H', ptbuf[6:8])[0]
        t.f_identifier = ptbuf[8:8+t.len_di]

        is_root = False;
        if t.len_di == 1:
            is_root = struct.unpack('B', ptbuf[8:9])[0]
            if is_root == 0 or is_root == 1:
                print "is a root directory(%d)" %(is_root)
            
        print "%d->length of identify:(%d), length of extend attribute:(%d), local:(%d)->(0x%x), parent dir number:(%d), identify:(%s)\n" \
            %(i, t.len_di, t.len_eattr, t.loc_extent, t.loc_extent*BLOCK_SIZE, t.pdir_nr, t.f_identifier)

        if t.len_di % 2 :
            len_pd = 1
        else:
            len_pd = 0

        r_size += 9+t.len_di-1+len_pd;
        if r_size >= total:         
            break;
        ptbuf = ptbuf[9+t.len_di-1+len_pd:]

def dump_primary_volume(volume_dsc):
    """ Dump primary volume descriptor """

    global BLOCK_SIZE

    print "===== Dump promary volume descriptor =="
    sys_identifier = volume_dsc[8:40]
    print "System Identifier:(%s)" %sys_identifier

    vol_identifier = volume_dsc[40:72]
    print "Volume Identifier:(%s)" %vol_identifier

    vol_size = struct.unpack('L',volume_dsc[80:84])[0]
    print "Volume Space size:(0x%x)BLOCKS(2kB)" %vol_size

    vol_seq = struct.unpack('H',volume_dsc[124:126])[0]
    print "Volume sequence number:(%d)" %(vol_seq)

    BLOCK_SIZE = struct.unpack('H',volume_dsc[128:130])[0]
    print "logic block size:(0x%x)" %(BLOCK_SIZE)

    
    pt_size = struct.unpack('L',volume_dsc[132:136])[0]
    pt_L_rd = struct.unpack('L',volume_dsc[140:144])[0]
    print "Volume path talbe L's BLOCK number is :(0x%x-->0x%x)" %(pt_L_rd, pt_L_rd*BLOCK_SIZE)

    print "Abstract File Identifier: (%s)" %(volume_dsc[739:776])
    print "Bibliographic File Identifier: (%s)" %(volume_dsc[776:813])

    f_ver = struct.unpack('B', volume_dsc[881])[0]
    print "File Structure Version:(%d)" %(f_ver)

    dump_pathtable_L(pt_L_rd, pt_size)

    (root_loc,root_total) = dump_filedir_record(volume_dsc[156:190])
    print "Root directory is at (%d)block, have(0x%x)bytes" %(root_loc, root_total)

    dump_filedir_record(None, root_loc, root_total)
#    dump_filedir_record(None, 23, 1)

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
    if len(sys.argv) < 2:
        usage()

    F_ISO = open(sys.argv[1], 'rb')

    desc_nr = 0;
    while F_ISO:
        desc_nr = desc_nr + 1;
        F_ISO.seek(BLOCK_SIZE*(15+desc_nr))
        volume_dsc = F_ISO.read(BLOCK_SIZE)
    
        flag = struct.unpack('B',volume_dsc[0])[0]
        if flag == 0:
            dump_boot_record(volume_dsc)
            continue

        if flag == 1:                                       
            dump_primary_volume(volume_dsc)
            continue

        if flag == 255:
            break;
