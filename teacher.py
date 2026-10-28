"""Sequence-level knowledge distillation data, original frozen Qwen via stdio."""
import json,pathlib,subprocess,time,resource,re,sys,hashlib
R=pathlib.Path(__file__).resolve().parent;R16=pathlib.Path('/home/carlos/qwen3.5-0.8b/laboratorio-cognitivo/ronda16')
B=R16/'engine/motor';M=pathlib.Path('/home/carlos/models/Qwen3.5-0.8B-Q8_0.gguf')

def prompt(question):
 return '<|im_start|>system\nYou are a calculator. Reply with only the integer result, with no words or reasoning.<|im_end|>\n<|im_start|>user\n'+question+'<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
def shafile(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def main(splits):
 if 'test' in splits:assert (R/'CHECKPOINTS-FREEZE.json').exists(),'freeze student before obtaining TEST teacher'
 config=dict(model_sha256=shafile(M),binary_sha256=shafile(B),max_new=8,temperature=0,seed='deterministic argmax',context=2048,thinking='closed')
 (R/'TEACHER-CACHE-CONFIG.json').write_text(json.dumps(config,indent=2)+'\n')
 log=(R/'teacher-engine.log').open('a');t=time.perf_counter();p=subprocess.Popen([str(B),str(M),'2048'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,text=True,bufsize=1)
 def call(**r):
  p.stdin.write(json.dumps(r)+'\n');p.stdin.flush();out=json.loads(p.stdout.readline());assert 'error' not in out,out;return out
 try:
  call(op='tokenize',text='startup');startup=time.perf_counter()-t
  for split in splits:
   target=R/'data'/f'teacher-{split}.jsonl';completed={json.loads(l)['id']:json.loads(l) for l in target.read_text().splitlines()} if target.exists() else {}
   cache_index=json.loads((R/'TEACHER-CACHE-INDEX.json').read_text()) if (R/'TEACHER-CACHE-INDEX.json').exists() else {}
   with target.open('a') as f:
    for row in json.loads((R/'data'/f'{split}.json').read_text()):
     expected_key=hashlib.sha256(json.dumps(dict(config=config,full_prompt=prompt(row['prompt'])),sort_keys=True).encode()).hexdigest()
     if row['id'] in completed:
      prior=completed[row['id']];actual_key=prior.get('request_key',cache_index.get(split+':'+row['id'],{}).get('request_key'));assert actual_key==expected_key,'Teacher cache request hash mismatch or absent';continue
     result=call(op='qa',method='baseline',prompt=prompt(row['prompt']),max_new=8)
     raw=result['text'].strip();parsed=bool(re.fullmatch(r'[+-]?\d+',raw));canonical=str(int(raw)) if parsed else raw
     usable=parsed and len(canonical.encode('utf8'))<=8 and bool(canonical)
     request_key=hashlib.sha256(json.dumps(dict(config=config,full_prompt=prompt(row['prompt'])),sort_keys=True).encode()).hexdigest()
     record={'request_key':request_key,**row,'teacher_raw':raw,'teacher_target':canonical,'strict_integer':parsed,'kd_usable':usable,'teacher_correct':parsed and int(raw)==int(row['answer']),'telemetry':result}
     f.write(json.dumps(record)+'\n');f.flush();print(split,row['id'],repr(raw),round(result['seconds'],2),flush=True)
 finally:
  p.stdin.close();p.wait(timeout=30);log.close()
  (R/f'teacher-{splits[0]}-cost.json').write_text(json.dumps(dict(wall_seconds=time.perf_counter()-t,startup_seconds=locals().get('startup'),child_cpu_total_seconds=resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime+resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime,child_peak_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,return_code=p.returncode,binary=str(B),model=str(M)),indent=2)+'\n')
if __name__=='__main__':main(sys.argv[1:] or ['train','dev'])
