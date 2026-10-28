"""Bounded phase runner with sampled process-tree RSS/swap and append-only records."""
import argparse,datetime,hashlib,json,os,pathlib,resource,subprocess,time
R=pathlib.Path(__file__).resolve().parent

def mem():
 out={}
 for l in pathlib.Path('/proc/meminfo').read_text().splitlines():
  k,v=l.split(':',1)
  if k in ['MemAvailable','SwapTotal','SwapFree']:out[k+'_kib']=int(v.split()[0])
 return out

def tree_usage(pid):
 infos={}
 for p in pathlib.Path('/proc').glob('[0-9]*'):
  try:
   st=(p/'status').read_text().splitlines();values={l.split(':')[0]:l.split(':',1)[1].strip() for l in st if ':' in l};infos[int(p.name)]=(int(values['PPid']),int(values.get('VmRSS','0 kB').split()[0]),int(values.get('VmSwap','0 kB').split()[0]))
  except (OSError,ValueError):pass
 include={pid};prev=set()
 while include!=prev:
  prev=include.copy();include|={i for i,(p,_,_) in infos.items() if p in include}
 return sum(infos.get(i,(0,0,0))[1] for i in include),sum(infos.get(i,(0,0,0))[2] for i in include)

def main():
 a=argparse.ArgumentParser();a.add_argument('phase');a.add_argument('command',nargs=argparse.REMAINDER);args=a.parse_args();assert args.command
 cmd=args.command[1:] if args.command[0]=='--' else args.command
 before=mem();start=time.perf_counter();cpu0=resource.getrusage(resource.RUSAGE_CHILDREN);log=R/f'{args.phase}.log';peakrss=peakswap=0;utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with log.open('a') as f:
  p=subprocess.Popen(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT)
  while p.poll() is None:
   rss,swap=tree_usage(p.pid);peakrss=max(peakrss,rss);peakswap=max(peakswap,swap);time.sleep(.2)
 after=resource.getrusage(resource.RUSAGE_CHILDREN)
 record=dict(phase=args.phase,started_utc=utc,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command=cmd,return_code=p.returncode,wall_seconds=time.perf_counter()-start,child_user_cpu_seconds=after.ru_utime-cpu0.ru_utime,child_system_cpu_seconds=after.ru_stime-cpu0.ru_stime,child_peak_rss_kib_rusage=after.ru_maxrss,sampled_tree_peak_rss_kib=peakrss,sampled_tree_peak_swap_kib=peakswap,rss_sampling_seconds=.2,machine_before=before,machine_after=mem(),log=str(log),protocol_sha256=hashlib.sha256((R/'PROTOCOLO.json').read_bytes()).hexdigest(),seed=170020)
 with (R/'RUNS.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
 (R/f'{args.phase}-RUN.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2));raise SystemExit(p.returncode)
if __name__=='__main__':main()
