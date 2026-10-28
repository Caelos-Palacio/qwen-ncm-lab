"""Run saved mini-NCM on a prompt without the teacher or arithmetic solver."""
import os
os.environ['OMP_NUM_THREADS']='2'
import argparse,json,time
import torch
from modelo import R,encode,decode,tokenizer,generator,generate
p=argparse.ArgumentParser();p.add_argument('prompt');p.add_argument('--model',choices=['kd','supervised','untrained','joint','continued'],default='kd');a=p.parse_args();torch.set_num_threads(2)
s=torch.load(R/f'{a.model}.pt',weights_only=True);vq=tokenizer();vq.load_state_dict(s['tokenizer']);vq.eval();g=generator(vq);g.load_state_dict(s['generator']);g.eval();x=torch.tensor([encode(a.prompt,64)]);start=time.perf_counter()
with torch.no_grad():out,codes=generate(vq,g,x)
text,ok=decode(out[0].tolist());print(json.dumps(dict(text=text,valid_utf8=ok,codes=codes.tolist(),seconds=time.perf_counter()-start,steps=4)))
