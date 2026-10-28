import os
os.environ['OMP_NUM_THREADS']='2';os.environ['OPENBLAS_NUM_THREADS']='1'
import json,time,re,hashlib,resource,statistics
import torch
from modelo import R,SEED,PAD,LEVELS,encode,decode,tokenizer,generator,generate

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def valid_integer(s):return bool(re.fullmatch(r'[+-]?\d+',s))
def correct(s,r):return valid_integer(s) and int(s)==int(r['answer'])
def agreement(s,r):return valid_integer(s) and r['strict_integer'] and int(s)==int(r['teacher_target'])
def summary(records):
 return {k:sum(r[k] for r in records)/len(records) for k in ['correct','teacher_agreement','valid_utf8','strict_integer']}
def main():
 torch.set_num_threads(2);freeze=json.loads((R/'CHECKPOINTS-FREEZE.json').read_text())
 assert not freeze['test_used_for_selection'] and not freeze['test_teacher_obtained']
 for file,h in freeze['files'].items():
  # data names are source-local because freeze keys are basenames.
  p=R/file if (R/file).exists() else R/'data'/file
  assert sha(p)==h,f'Changed frozen artifact {file}'
 rows=[json.loads(l) for l in (R/'data/teacher-test.jsonl').read_text().splitlines()];train=[json.loads(l) for l in (R/'data/teacher-train.jsonl').read_text().splitlines()];assert len(rows)==64
 pred=[];costs={};codeuse={};tok=tokenizer();state=torch.load(R/'kd.pt',weights_only=True);tok.load_state_dict(state['tokenizer']);tok.eval()
 for p in tok.parameters():p.requires_grad=False
 prefix=torch.tensor([encode(r['prompt'],64) for r in rows]);teacher=[]
 for row in rows:
  s=row['teacher_raw'];teacher.append(dict(id=row['id'],correct=correct(s,row),teacher_agreement=True,valid_utf8=True,strict_integer=valid_integer(s),text=s,template=row['template']))
 pred.extend({'method':'teacher',**r} for r in teacher)
 for method in ['kd','supervised','untrained','joint','continued']:
  state=torch.load(R/f'{method}.pt',weights_only=True);tok.load_state_dict(state['tokenizer']);tok.eval();gen=generator(tok);gen.load_state_dict(state['generator']);gen.eval();records=[];timings=[];cpu=[];codes_all=[]
  with torch.no_grad():
   generate(tok,gen,prefix[:1])
   for i,row in enumerate(rows):
    wall=time.perf_counter();c=time.process_time();output,codes=generate(tok,gen,prefix[i:i+1]);timings.append(time.perf_counter()-wall);cpu.append(time.process_time()-c);text,ok=decode(output[0].tolist());codes_all.append(codes[0]);records.append(dict(id=row['id'],text=text,valid_utf8=ok,strict_integer=valid_integer(text),correct=correct(text,row),teacher_agreement=agreement(text,row),template=row['template'],wall_seconds=timings[-1],cpu_seconds=cpu[-1]))
  pred.extend({'method':method,**r} for r in records);costs[method]=dict(mean_wall_seconds=statistics.mean(timings),median_wall_seconds=statistics.median(timings),mean_cpu_seconds=statistics.mean(cpu),sum_wall_seconds=sum(timings),parameters=sum(p.numel() for p in gen.parameters())+sum(p.numel() for p in tok.parameters()),checkpoint_bytes=(R/f'{method}.pt').stat().st_size,p95_wall_seconds=sorted(timings)[int(.95*(len(timings)-1))],batch=1,threads=2,scope='prompt embedding + 4 scales + VQVAE decode; model already loaded; one warmup excluded')
  codes_all=torch.stack(codes_all);offset=0;codeuse[method]=[]
  for size in LEVELS:
   counts=torch.bincount(codes_all[:,offset:offset+size].flatten(),minlength=64).float();p=counts/counts.sum();entropy=float(-(p[p>0]*p[p>0].log()).sum());codeuse[method].append(dict(level_length=size,used_codes=int((counts>0).sum()),codebook_size=64,entropy_nats=entropy,dominant_code_fraction=float(counts.max()/counts.sum())));offset+=size
  print(method,summary(records),costs[method],flush=True)
 for row in rows:
  closest=min((t for t in train if t['op']==row['op']),key=lambda t:(abs(t['a']-row['a'])+abs(t['b']-row['b']),t['id']));text=closest['teacher_target'];pred.append(dict(method='nearest_train',id=row['id'],text=text,correct=correct(text,row),teacher_agreement=agreement(text,row),valid_utf8=True,strict_integer=valid_integer(text),template=row['template'],source_train_id=closest['id']))
 (R/'PREDICCIONES.json').write_text(json.dumps(pred,indent=2)+'\n');(R/'PREDICCIONES-FREEZE.json').write_text(json.dumps(dict(sha256=sha(R/'PREDICCIONES.json'),records=len(pred),checkpoints_sha256=sha(R/'CHECKPOINTS-FREEZE.json')),indent=2)+'\n')
 bymethod={m:[r for r in pred if r['method']==m] for m in ['teacher','kd','supervised','untrained','joint','continued','nearest_train']};metrics={m:{'all':summary(rs),**{tpl:summary([r for r in rs if r['template']==tpl]) for tpl in ['seen','unseen']},'by_operation':{op:summary([r for r in rs if next(q['op'] for q in rows if q['id']==r['id'])==op]) for op in ['+','-','*']}} for m,rs in bymethod.items()}
 # Reconstruction is separate, and cannot count as free generation.
 tok.load_state_dict(torch.load(R/'kd.pt',weights_only=True)['tokenizer']);target=torch.tensor([encode(r['teacher_target'],8) for r in rows if r['kd_usable']]);tok.eval()
 with torch.no_grad():
  enc=tok.encode(target);recon=tok.decode(enc).argmax(-1);mask=target!=PAD;reconstruction=dict(sequences=len(target),full_byte_exact=float((recon==target).all(-1).float().mean()),nonpad_char_accuracy=float((recon[mask]==target[mask]).float().mean()))
 result=dict(metrics=metrics,costs=costs,codebook_usage_generated=codeuse,tokenizer_reconstruction_only=reconstruction,process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,test_questions=64,test_selection_before_teacher=True,teacher_cost_file='teacher-test-cost.json',scope='restricted integer arithmetic only; 8-byte output, not a chat model; CPU comparison with Qwen differs in parameter count and runtime')
 (R/'PREDICCIONES.json').write_text(json.dumps(pred,indent=2)+'\n');(R/'RESULTADOS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(metrics,indent=2))
if __name__=='__main__':main()
