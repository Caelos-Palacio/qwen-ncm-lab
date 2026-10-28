"""Two-stage NCM training using unmodified official model implementations."""
import os
os.environ['OMP_NUM_THREADS']='2';os.environ['OPENBLAS_NUM_THREADS']='1'
import json,time,pathlib,random,hashlib,resource,copy
import torch
import re
import torch.nn.functional as F
from modelo import R,SEED,PAD,LEVELS,encode,decode,tokenizer,generator,training_inputs,generate

def dump(name,obj):(R/name).write_text(json.dumps(obj,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(s):return [json.loads(l) for l in (R/'data'/f'teacher-{s}.jsonl').read_text().splitlines()]
def tensor(data,key,n):return torch.tensor([encode(r[key],n) for r in data])
def accuracy(pred,data,key='answer'):
 decoded=[decode(x.tolist()) for x in pred]; exact=sum(bool(valid and re.fullmatch(r'[+-]?\d+',s) and re.fullmatch(r'[+-]?\d+',r[key]) and int(s)==int(r[key])) for (s,valid),r in zip(decoded,data))/len(data)
 return exact

def ckpt(vq,gen=None):
 return dict(tokenizer=vq.state_dict(),generator=gen.state_dict() if gen else None,seed=SEED,upstream_commit='c70274273f489abc73832b2b98584a8483b6b203')

def main():
 torch.set_num_threads(2);torch.manual_seed(SEED);random.seed(SEED)
 assert not (R/'CHECKPOINTS-FREEZE.json').exists(),'Frozen run: do not retrain'
 tr=rows('train');dv=rows('dev');usable=[r for r in tr if r['kd_usable']]
 assert len(usable)>=150 and len(dv)==32
 dv_usable=[r for r in dv if r['kd_usable']];assert dv_usable
 vq=tokenizer();x=tensor(usable,'teacher_target',8);xd=tensor(dv_usable,'teacher_target',8)
 params=sum(p.numel() for p in vq.parameters());history=[];start=time.perf_counter();cpu=time.process_time();opt=torch.optim.AdamW([p for p in vq.parameters() if p.requires_grad],lr=.002,weight_decay=.01)
 best=-1;plateau=0;scout_start=time.perf_counter()
 for step in range(1,1501):
  vq.train();batch=x[torch.randint(len(x),(32,))];logits,vqloss,*_=vq(batch);loss=F.cross_entropy(logits.flatten(0,1),batch.flatten())+vqloss;assert torch.isfinite(loss)
  opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(vq.parameters(),1.);opt.step()
  if step==50:dump('SCOUT-TOKENIZER.json',dict(actual_steps=50,included_in_budget=True,wall_seconds=time.perf_counter()-scout_start,cpu_seconds=time.process_time()-cpu,projected_1500_seconds=(time.perf_counter()-scout_start)*30,process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
  if step%100==0:
   vq.eval()
   with torch.no_grad():
    # no mutation of EMA: encode and decode instead of forward
    recon=vq.decode(vq.encode(xd)).argmax(-1);acc=accuracy(recon,dv_usable,'teacher_target');nonpad=xd!=PAD;char=float((recon[nonpad]==xd[nonpad]).float().mean());hist=dict(step=step,loss=float(loss),dev_reconstruction_exact=acc,dev_nonpad_char=char);history.append(hist);print('TOKENIZER',hist,flush=True)
   if acc>best:
    best=acc;plateau=0;torch.save(ckpt(vq),R/'tokenizer.pt')
   else:plateau+=1
   if (acc==1. and step>=400) or (step>=400 and plateau>=4):break
 dump('TOKENIZER-FIT.json',dict(history=history,wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu,parameters=params,train_samples=len(x),train_steps=step,train_examples_seen=step*32,train_byte_positions_seen=step*32*8,process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,rejected_kd=[r['id'] for r in tr if not r['kd_usable']],rejected_dev_kd=[r['id'] for r in dv if not r['kd_usable']],selection='maximum DEV exact reconstruction; earliest tie'))
 vq.load_state_dict(torch.load(R/'tokenizer.pt',weights_only=True)['tokenizer']);vq.eval()
 for p in vq.parameters():p.requires_grad=False;p.grad=None
 # Supervised-reference baseline shares the frozen teacher-trained tokenizer; only generator targets differ.
 allfit={}
 for name,target in [('kd','teacher_target'),('supervised','answer')]:
  torch.manual_seed(SEED);gen=generator(vq);data=usable;prefix=tensor(data,'prompt',64);targets=tensor(data,target,8);dvp=tensor(dv,'prompt',64)
  with torch.no_grad():codes=vq.encode(targets);prefix_features=vq.encoder.wte(prefix).detach()
  torch.save(dict(codes=codes,prefix_features=prefix_features,prefix=prefix,targets=targets),R/f'CACHE-{name}.pt')
  if name=='kd':torch.save(ckpt(vq,gen),R/'untrained.pt')
  opt=torch.optim.AdamW(gen.parameters(),lr=.0005,weight_decay=.01);history=[];best=(-1.,float('-inf'));start=time.perf_counter();cpu=time.process_time();plateau=0;best_exact=-1
  for step in range(1,3001):
   gen.train();ix=torch.randint(len(data),(32,));inp,labels=training_inputs(vq,gen,targets[ix],prefix[ix],corrupt=True,target_codes=codes[ix],prefix_features=prefix_features[ix]);logits=gen(inp,prefix_pad_mask=prefix[ix]==PAD)
   offset=0;loss=0
   for size in LEVELS:
    loss+=F.cross_entropy(logits[:,offset:offset+size].reshape(-1,64),labels[:,offset:offset+size].reshape(-1))/len(LEVELS);offset+=size
   assert torch.isfinite(loss);opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(gen.parameters(),1.);opt.step()
   if step==50:dump(f'SCOUT-{name}.json',dict(actual_steps=50,included_in_budget=True,wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu,projected_3000_seconds=(time.perf_counter()-start)*60,process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
   if step%200==0:
    gen.eval()
    with torch.no_grad():
     pred,_=generate(vq,gen,dvp);acc=accuracy(pred,dv);agreement=accuracy(pred,dv,'teacher_target');valid_dv=dv_usable if name=='kd' else dv;valid_p=tensor(valid_dv,'prompt',64);di,dl=training_inputs(vq,gen,tensor(valid_dv,target,8),valid_p);dlog=gen(di,prefix_pad_mask=valid_p==PAD);devloss=float(F.cross_entropy(dlog.reshape(-1,64),dl.reshape(-1)));score=(acc,-devloss)
    h=dict(step=step,train_loss=float(loss),dev_free_exact=acc,dev_teacher_agreement=agreement,dev_code_ce=devloss);history.append(h);print(name,h,flush=True)
    if score>best:
     best=score;torch.save(ckpt(vq,gen),R/f'{name}.pt')
    if acc>best_exact:best_exact=acc;plateau=0
    else:plateau+=1
    if step>=600 and plateau>=3:break
  allfit[name]=dict(history=history,wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu,parameters=sum(p.numel() for p in gen.parameters()),train_samples=len(data),target=target,best_dev_exact=best[0],selection='max DEV free generation exact arithmetic; tie lower DEV code CE',training_steps=step,max_training_steps=3000,train_examples_seen=step*32,train_code_positions_seen=step*32*sum(LEVELS),early_stopping='minimum600steps,patience3 DEV exact evaluations every200; tieCE selects checkpoint but does not reset exact plateau',process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
  dump('GENERATOR-FIT.json',allfit)
 jointfit=fit_joint(vq,usable,dv)
 dump('JOINT-FIT.json',jointfit)
 manifest={p.name:sha(p) for p in [R/'tokenizer.pt',R/'kd.pt',R/'supervised.pt',R/'untrained.pt',R/'PROTOCOLO.json',R/'data/train.json',R/'data/dev.json',R/'data/test.json',R/'modelo.py',R/'train.py',R/'teacher.py',R/'evaluar.py',R/'inferir.py',R/'joint.py',R/'joint.pt',R/'continued.pt']}
 dump('CHECKPOINTS-FREEZE.json',dict(utc=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),files=manifest,test_teacher_obtained=(R/'data/teacher-test.jsonl').exists(),test_used_for_selection=False,process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
 print('CHECKPOINTS FROZEN',flush=True)

def fit_joint(vq,train,dev):
 from joint import loss as joint_loss,rollout
 results={};base=torch.load(R/'kd.pt',weights_only=True)
 prefix=tensor(train,'prompt',64);target=tensor(train,'teacher_target',8);devp=tensor(dev,'prompt',64)
 for mode in ['joint','continued']:
  torch.manual_seed(SEED+1);vq.load_state_dict(base['tokenizer']);vq.eval()
  for p in vq.parameters():p.requires_grad=False;p.grad=None
  if mode=='joint':
   for p in vq.decoder.parameters():p.requires_grad=True
  gen=generator(vq);gen.load_state_dict(base['generator']);gen.eval()
  with torch.no_grad():target_codes=vq.encode(target)
  with torch.no_grad():
   standard_codes=gen.generate(None,prefix[:3],temperature=0.,top_k=0,top_p=1.)
   _,_,st_codes=rollout(vq,gen,prefix[:3]);assert torch.equal(standard_codes,st_codes),'ST forward must match official hard inference'
  opt=torch.optim.AdamW([p for p in list(gen.parameters())+list(vq.decoder.parameters()) if p.requires_grad],lr=.0001,weight_decay=.01)
  hist=[];best=(-1.,float('-inf'));start=time.perf_counter();cpu=time.process_time();gradcheck=None
  for step in range(1,501):
   ix=torch.randint(len(train),(16,));gen.train();vq.decoder.train(mode=='joint')
   loss,textce,aux=joint_loss(vq,gen,prefix[ix],target[ix],labels=target_codes[ix]);assert torch.isfinite(loss);opt.zero_grad()
   if step==1:
    gs=torch.autograd.grad(textce,list(gen.parameters()),retain_graph=True,allow_unused=True);text_gen_norm=sum(float(g.square().sum()) for g in gs if g is not None)**.5;assert text_gen_norm>0
   loss.backward()
   if step==1:
    norm=lambda ps:sum(float(p.grad.square().sum()) for p in ps if p.grad is not None)**.5
    gradcheck=dict(generator_grad_norm=norm(gen.parameters()),decoder_grad_norm=norm(vq.decoder.parameters()),codebook_grad_norm=norm(vq.vq.embeddings.parameters()),encoder_grad_norm=norm(vq.encoder.parameters()),hard_forward_equals_official=True,text_only_generator_grad_norm=text_gen_norm)
    assert gradcheck['generator_grad_norm']>0 and gradcheck['encoder_grad_norm']==0 and gradcheck['codebook_grad_norm']==0
    assert (gradcheck['decoder_grad_norm']>0)==(mode=='joint')
   torch.nn.utils.clip_grad_norm_(gen.parameters(),1.);torch.nn.utils.clip_grad_norm_(vq.decoder.parameters(),1.);opt.step()
   if step==50:dump(f'SCOUT-{mode}.json',dict(actual_steps=50,included_in_budget=True,wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu,projected_500_seconds=(time.perf_counter()-start)*10,process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
   if step%100==0:
    gen.eval();vq.eval()
    with torch.no_grad():
     pred,_=generate(vq,gen,devp);acc=accuracy(pred,dev);score=(acc,-float(loss));h=dict(step=step,train_total_loss=float(loss),train_text_ce=float(textce),train_code_ce=float(aux),dev_free_exact=acc);hist.append(h);print(mode,h,flush=True)
    if score>best:best=score;torch.save(ckpt(vq,gen),R/f'{mode}.pt')
  results[mode]=dict(history=hist,gradient_check=gradcheck,wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu,training_steps=500,batch_size=16,parameters_trainable=sum(p.numel() for p in list(gen.parameters())+list(vq.decoder.parameters()) if p.requires_grad),process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,source_checkpoint_sha256=sha(R/'kd.pt'),scope='same start, same500steps and inputs; computation differs when decoder gradients enabled',best_dev_exact=best[0])
 return results

if __name__=='__main__':main()
