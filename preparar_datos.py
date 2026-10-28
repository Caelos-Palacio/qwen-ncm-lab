import hashlib,json,pathlib,datetime
R=pathlib.Path(__file__).resolve().parent

if (R/'ENTRADA-FREEZE.json').exists():raise SystemExit('Inputs frozen; do not regenerate protocol or splits')

def key(x):return hashlib.sha256(('NCM170020|'+x).encode()).hexdigest()
rows=[]
for op in ['+','-','*']:
 for a in range(31):
  for b in range(31):
   if op in ['+','*'] and b<a:continue
   rows.append(dict(id=f'{op}:{a}:{b}',op=op,a=a,b=b,answer=str(a+b if op=='+' else a-b if op=='-' else a*b)))
rows.sort(key=lambda r:key(r['id']))
used=set();splits={}
for split,n in [('train',192),('dev',32),('test',64)]:
 selected=[]
 for op in ['+','-','*']:
  count=n//3+(op=='+')*(n%3)
  take=[r.copy() for r in rows if r['op']==op and r['id'] not in used][:count]
  for r in take:used.add(r['id'])
  selected+=take
 selected.sort(key=lambda r:key('order|'+r['id']))
 for i,r in enumerate(selected):
  unseen=split=='test' and i>=32
  r['template']='unseen' if unseen else 'seen'
  r['prompt']=(f"Compute {r['a']} {r['op']} {r['b']}." if not unseen else f"Evaluate the expression {r['a']}{r['op']}{r['b']}.")
  r['prompt']+=' Integer only.'
  assert len(r['prompt'].encode())<=64
 splits[split]=selected
(R/'data').mkdir(exist_ok=True)
for s,rs in splits.items():(R/'data'/f'{s}.json').write_text(json.dumps(rs,indent=2)+'\n')
protocol={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'definition':'Next-Concept Modeling, HazyResearch/ncm','upstream_commit':'c70274273f489abc73832b2b98584a8483b6b203','paper':'https://arxiv.org/abs/2610.14162','license':'MIT','task':'integer arithmetic +,-,* operands0..30; experimental restricted model, not Qwen replacement','samples':{s:len(x) for s,x in splits.items()},'split_unit':'operation + operand pair, commutative mirror deduplicated; deterministic SHA256 NCM170020; no pair overlap','test_strata':'first32 same template, last32 entirely unseen template','teacher':'original Qwen3.5-0.8B-Q8_0, temp0,max_new8; raw outputs retained; strict full integer parse; only strict full integer outputs fitting8UTF8bytes admitted to KD; rejected IDs preserved, baseline exact uses same admitted TRAIN IDs; no teacher mistakes replaced','tokenizer':{'vocab':257,'pad':256,'context':8,'dimension':64,'levels':[1,2,4,8],'codebook_sizes':[64]*4,'steps_limit':1500,'loss':'CE reconstruction+officialVQ commitment, official nested dropout'},'generator':{'dimension':128,'layers':4,'heads':4,'prefix_bytes':64,'steps_limit':3000,'seed':170020,'train_batch':32,'threads':2,'loss':'per-level mean CE; true codes only as targets; previous cumulative codes as conditioning','selection':'DEV free generation exact integer, tie lower CE; no TEST teacher until generator checkpoint frozen'},'baselines':['same architecture trained exact arithmetic reference without KD','untrained generator','nearest TRAIN prompt response'],'status':'frozen before teacher extraction and all training'}
(R/'PROTOCOLO.json').write_text(json.dumps(protocol,indent=2)+'\n')
print(protocol['samples'])
