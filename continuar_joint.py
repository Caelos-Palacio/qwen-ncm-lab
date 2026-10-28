"""Continue after planned removal of optional full supervised training."""
import os
os.environ['OMP_NUM_THREADS']='2';os.environ['OPENBLAS_NUM_THREADS']='1'
import datetime,json,pathlib,torch
from modelo import R,SEED,tokenizer
from train import fit_joint,rows,dump,sha

def main():
 torch.set_num_threads(2);torch.manual_seed(SEED)
 assert not (R/'CHECKPOINTS-FREEZE.json').exists()
 vq=tokenizer();data=[r for r in rows('train') if r['kd_usable']];dev=rows('dev')
 result=fit_joint(vq,data,dev);dump('JOINT-FIT.json',result)
 files=[R/n for n in ['tokenizer.pt','kd.pt','supervised.pt','untrained.pt','joint.pt','continued.pt','PROTOCOLO.json','PROTOCOLO.md','modelo.py','train.py','teacher.py','evaluar.py','inferir.py','joint.py','continuar_joint.py','data/train.json','data/dev.json','data/test.json']]
 dump('CHECKPOINTS-FREEZE.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files={str(p.relative_to(R)):sha(p) for p in files},test_teacher_obtained=(R/'data/teacher-test.jsonl').exists(),test_used_for_selection=False,supervised_status='exploratory checkpoint200; interrupted partial run, unequal budget',partial_run_cost_file='PARADA-PLANIFICADA.json'))
 print('ALL CHECKPOINTS FROZEN',flush=True)
if __name__=='__main__':main()
