import os
import sys
from PIL import Image
d=open(os.environ.get('HM_ROM','Harvest_Moon_-_Friends_of_Mineral_Town__USA_.gba'),'rb').read()
PAL=[(255,255,255),(0,0,0),(200,40,40),(40,160,40),(40,60,200),(230,200,30),(150,60,200),(30,190,190),(240,130,30),(120,80,40),(255,150,190),(120,120,120),(60,100,60),(100,170,255),(190,190,190),(255,230,170)]
def render(start,length,per_row=32,scale=2,mode='obj16',out='sheet.png'):
    n=length//128
    rows=(n+per_row-1)//per_row
    img=Image.new('RGB',(per_row*16,rows*16),(255,255,255))
    px=img.load()
    for i in range(n):
        base=start+i*128
        sx=(i%per_row)*16; sy=(i//per_row)*16
        for t in range(4):                 # 1D OBJ mapping: tiles 0,1 top row; 2,3 bottom row
            tx=(t%2)*8; ty=(t//2)*8
            tb=base+t*32
            for y in range(8):
                for x in range(4):
                    b=d[tb+y*4+x]
                    px[sx+tx+x*2,sy+ty+y]=PAL[b&15]; px[sx+tx+x*2+1,sy+ty+y]=PAL[b>>4]
    img=img.resize((img.width*scale,img.height*scale),Image.NEAREST); img.save(out); print(out,img.size)
if __name__=='__main__':
    s=int(sys.argv[1],16); l=int(sys.argv[2],16); render(s,l,out=sys.argv[3])
