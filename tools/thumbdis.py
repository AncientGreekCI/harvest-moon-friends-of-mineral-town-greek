import os
from capstone import *
import struct,re,sys
d=open(os.environ.get('HM_ROM','Harvest_Moon_-_Friends_of_Mineral_Town__USA_.gba'),'rb').read()
md=Cs(CS_ARCH_ARM,CS_MODE_THUMB); md.skipdata=True
def dis(a,b):
    for i in md.disasm(d[a:b],0x08000000+a):
        extra=''
        if i.mnemonic=='ldr' and 'pc' in i.op_str:
            m=re.search(r'#(0x[0-9a-f]+)',i.op_str)
            if m:
                lit=((i.address-0x08000000+4)&~3)+int(m.group(1),0)
                extra='   ; =0x%08x'%struct.unpack_from('<I',d,lit)[0]
        print('%06x: %-6s %s%s'%(i.address-0x08000000,i.mnemonic,i.op_str,extra))
if __name__=='__main__':
    dis(int(sys.argv[1],16),int(sys.argv[2],16))
