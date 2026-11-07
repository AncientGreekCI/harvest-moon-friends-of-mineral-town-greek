import os
import sys
from PIL import Image
d=open(os.environ.get('HM_ROM','Harvest_Moon_-_Friends_of_Mineral_Town__USA_.gba'),'rb').read()
PAL=[(255,0,255),(0,0,0),(200,40,40),(40,160,40),(40,60,200),(230,200,30),(150,60,200),(30,190,190),(240,130,30),(120,80,40),(255,150,190),(120,120,120),(60,100,60),(100,170,255),(190,190,190),(255,230,170)]
def render(start,length,wide=32,scale=3,out='t.png'):
    n=length//32; rows=(n+wide-1)//wide
    img=Image.new('RGB',(wide*8,rows*8),(255,0,255)); px=img.load()
    for i in range(n):
        b=start+i*32; sx=(i%wide)*8; sy=(i//wide)*8
        for y in range(8):
            for x in range(4):
                v=d[b+y*4+x]; px[sx+x*2,sy+y]=PAL[v&15]; px[sx+x*2+1,sy+y]=PAL[v>>4]
    img=img.resize((img.width*scale,img.height*scale),Image.NEAREST); img.save(out); print(out,img.size)
s=int(sys.argv[1],16); l=int(sys.argv[2],16); render(s,l,int(sys.argv[4]) if len(sys.argv)>4 else 32,out=sys.argv[3])
