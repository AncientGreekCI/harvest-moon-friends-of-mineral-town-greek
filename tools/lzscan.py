import os
import struct, collections, pickle
d=open(os.environ.get('HM_ROM','Harvest_Moon_-_Friends_of_Mineral_Town__USA_.gba'),'rb').read()
N=len(d)
def lz77(p):
    size=d[p+1]|d[p+2]<<8|d[p+3]<<16
    if size<32 or size>0x30000: return None
    out=bytearray(); q=p+4
    try:
        while len(out)<size:
            fl=d[q]; q+=1
            for k in range(8):
                if len(out)>=size: break
                if fl&(0x80>>k):
                    b1=d[q]; b2=d[q+1]; q+=2
                    ln=(b1>>4)+3; disp=((b1&15)<<8|b2)+1
                    if disp>len(out): return None
                    for _ in range(ln): out.append(out[-disp])
                else:
                    out.append(d[q]); q+=1
    except IndexError: return None
    if len(out)!=size and len(out)>size+16: return None
    return bytes(out[:size]), q-p
hits=[]
p=0
while True:
    p=d.find(b'\x10',p)
    if p<0 or p>N-8: break
    r=lz77(p)
    if r and r[1]>=16 and r[1] < len(r[0]):   # must actually compress
        hits.append((p,len(r[0]),r[1]))
    p+=1
print('LZ77 candidates:',len(hits))
sizes=collections.Counter(h[1] for h in hits)
print('most common decompressed sizes:',sizes.most_common(12))
pickle.dump(hits,open('lzhits.pkl','wb'))
al=[h for h in hits if h[0]%4==0]; print('4-aligned:',len(al),' 2-aligned:',len([h for h in hits if h[0]%2==0]))
