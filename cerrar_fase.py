"""Finish already-frozen phase serially; no new experiments or fitting."""
import json,pathlib,subprocess,time,sys,hashlib
R=pathlib.Path(__file__).resolve().parent
PY='/home/carlos/qwen3.5-0.8b/laboratorio-cognitivo/ronda17/ncm/.venv/bin/python'

def phase(name,script,*args):
 subprocess.run([PY,str(R/'ejecutar_fase.py'),name,'--',PY,str(R/script),*args],check=True,cwd=R)

def main():
 while not (R/'joint-fit-RUN.json').exists():time.sleep(1)
 assert json.loads((R/'joint-fit-RUN.json').read_text())['return_code']==0
 freeze=json.loads((R/'CHECKPOINTS-FREEZE.json').read_text());assert not freeze['test_used_for_selection'] and not freeze['test_teacher_obtained']
 for file,h in freeze['files'].items():assert hashlib.sha256((R/file).read_bytes()).hexdigest()==h,file
 phase('teacher-test','teacher.py','test')
 phase('evaluacion','evaluar.py')
 subprocess.run([sys.executable,str(R/'informe.py')],check=True,cwd=R)
 print('PHASE0+0.1 COMPLETE',flush=True)
if __name__=='__main__':main()
