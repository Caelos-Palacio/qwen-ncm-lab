"""Experimental joint adaptation, hard-forward/soft-backward NCM rollout.
Official model classes remain unmodified. This path explicitly reconstructs the
otherwise no_grad inference operations so text loss reaches the generator.
"""
import torch
import torch.nn.functional as F
from modelo import LEVELS

def rollout(vq,gen,prefix):
 B=len(prefix);P=gen.prefix_len
 emb=gen.transformer.wte(vq.encoder.wte(prefix))
 if not gen.use_rope:emb=emb+gen.wpe(gen.wp_prefix)
 pad=prefix==gen.prefix_pad_id
 zhat=torch.zeros(B,LEVELS[-1],vq.embed_dim)
 logits_all=[];codes_all=[];offset=0
 for k,length in enumerate(LEVELS):
  low=gen.build_l0_query_input(B) if k==0 else F.interpolate(zhat.transpose(1,2),size=length,mode='area').transpose(1,2)
  x=gen.transformer.wte(low)
  if not gen.use_rope:x=x+gen.wpe(gen.wp_1L[:,offset:offset+length])
  if gen.config.use_level_encoding:x=x+gen.transformer.wle(gen.lvl_1L[:,offset:offset+length])
  h=torch.cat([emb,x],dim=1);mask=torch.zeros(B,1,P+length,P+length);mask[:,:,:P,P:]=float('-inf');mask[:,:,:,:P]=mask[:,:,:,:P].masked_fill(pad[:,None,None,:],float('-inf'))
  rope=(getattr(gen,f'rope_cos_gen_{k}'),getattr(gen,f'rope_sin_gen_{k}')) if gen.use_rope else None
  for block in gen.transformer.blocks:h=block(h,attn_mask=mask,rope_cos_sin=rope)
  logits=gen.lm_heads[k](gen.transformer.ln_f(h)[:,P:]);soft=logits.softmax(-1);hard=F.one_hot(soft.argmax(-1),64).to(soft.dtype);st=hard+soft-soft.detach()
  q=st@vq.vq.embeddings[k].weight
  up=vq.vq._up_to_full(q,k,LEVELS[-1]) if k<len(LEVELS)-1 else q
  zhat=zhat+vq.vq._apply_quant_resi(up,k)
  logits_all.append(logits);codes_all.append(hard.argmax(-1));offset+=length
 return vq.decoder(zhat),logits_all,torch.cat(codes_all,dim=1)

def loss(vq,gen,prefix,target,labels=None):
 logits,codelogits,codes=rollout(vq,gen,prefix)
 if labels is None:
  with torch.no_grad():labels=vq.encode(target)
 text_ce=F.cross_entropy(logits.reshape(-1,257),target.reshape(-1));aux=0;offset=0
 for length,cl in zip(LEVELS,codelogits):
  aux+=F.cross_entropy(cl.reshape(-1,64),labels[:,offset:offset+length].reshape(-1))/len(LEVELS);offset+=length
 return text_ce+.25*aux,text_ce,aux
