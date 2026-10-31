import sys, msgpack
a=msgpack.unpackb(open(sys.argv[1],'rb').read(), raw=False, strict_map_key=False)
b=msgpack.unpackb(open(sys.argv[2],'rb').read(), raw=False, strict_map_key=False)
def walk(x,y,p):
    if type(x)!=type(y): print("TYPE",p,type(x),type(y)); return
    if isinstance(x,dict):
        if list(x)!=list(y): print("KEYORDER" if set(x)==set(y) else "KEYS",p, list(x)[:6], list(y)[:6])
        for k in x:
            if k in y: walk(x[k],y[k],p+"."+str(k))
    elif isinstance(x,list):
        if len(x)!=len(y): print("LEN",p); return
        for i,(u,v) in enumerate(zip(x,y)): walk(u,v,f"{p}[{i}]")
    elif x!=y: print("DIFF",p,repr(x)[:100],repr(y)[:100])
walk(a,b,"")
