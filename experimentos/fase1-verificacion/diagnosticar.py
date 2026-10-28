"""Diagnóstico acotado de checkpoints congelados, sin entrenamiento ni TEST."""
import os
os.environ['OMP_NUM_THREADS'] = '2'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
import hashlib
import json
import pathlib
import re
import resource
import sys
import time
import threading
import torch
import torch.nn.functional as F

OUT = pathlib.Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT))
from modelo import PAD, LEVELS, encode, decode, tokenizer, generator, generate, training_inputs
from joint import rollout

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify_frozen():
    freeze = json.loads((ROOT / 'CHECKPOINTS-FREEZE.json').read_text())
    checked = {}
    for name, expected in freeze['files'].items():
        path = ROOT / name
        if not path.exists():
            path = ROOT / 'data' / name
        checked[str(path.relative_to(ROOT))] = sha(path)
        assert checked[str(path.relative_to(ROOT))] == expected, name
    return checked

def tensor(rows, key, length):
    return torch.tensor([encode(row[key], length) for row in rows])

def metrics(output, rows, target):
    texts = [decode(row.tolist()) for row in output]
    valid = [ok and bool(re.fullmatch(r'[+-]?\d+', text)) for text, ok in texts]
    mask = target != PAD
    return dict(n=len(rows), arithmetic_exact=sum(ok and int(text[0]) == int(row['answer']) for text, ok, row in zip(texts, valid, rows)), teacher_text_exact=sum(text[0] == row['teacher_target'] for text, row in zip(texts, rows)), integer_parse=sum(valid), valid_utf8=sum(text[1] for text in texts), nonpad_correct=int((output[mask] == target[mask]).sum()), nonpad_total=int(mask.sum()), full_bytes_exact=int((output == target).all(-1).sum()))

def add_metrics(total, batch):
    for key, value in batch.items():
        total[key] = total.get(key, 0) + value

def main():
    torch.set_num_threads(2)
    torch.manual_seed(170021)
    wall, cpu = time.perf_counter(), time.process_time()
    memory = dict(peak_swap_kib=0, samples=0)
    stopped = threading.Event()
    def sample_memory():
        while not stopped.is_set():
            status = pathlib.Path('/proc/self/status').read_text()
            swap = int(re.search(r'VmSwap:\s+(\d+)', status).group(1))
            memory['peak_swap_kib'] = max(memory['peak_swap_kib'], swap)
            memory['samples'] += 1
            stopped.wait(.2)
    monitor = threading.Thread(target=sample_memory, daemon=True)
    monitor.start()
    initial_hashes = verify_frozen()
    protocol_hash = sha(OUT / 'PROTOCOLO.json')
    datasets = {split: [json.loads(line) for line in (ROOT / 'data' / f'teacher-{split}.jsonl').read_text().splitlines()] for split in ['train', 'dev']}
    result = dict(protocol_sha256=protocol_hash, initial_hashes=initial_hashes, data_sha256={split: sha(ROOT / 'data' / f'teacher-{split}.jsonl') for split in datasets}, methods={})
    predictions = []
    for method in ['kd', 'joint', 'continued', 'supervised', 'untrained']:
        method_wall = time.perf_counter()
        state = torch.load(ROOT / f'{method}.pt', weights_only=True)
        vq = tokenizer(); vq.load_state_dict(state['tokenizer']); vq.eval()
        gen = generator(vq); gen.load_state_dict(state['generator']); gen.eval()
        for parameter in vq.parameters():
            parameter.requires_grad = False
        condition = dict(parameters_generator=sum(p.numel() for p in gen.parameters()), parameters_codec=sum(p.numel() for p in vq.parameters()), splits={})
        with torch.no_grad():
            for split, rows in datasets.items():
                aggregate = dict(free={}, teacher_forced={}, reconstruction={}, code_levels=[dict(correct=0, total=0, ce_sum=0., free_correct=0) for _ in LEVELS])
                for start in range(0, len(rows), 16):
                    batch = rows[start:start+16]
                    prefix = tensor(batch, 'prompt', 64)
                    # Free metrics cover every prompt, including rejected teacher strings.
                    target = tensor(batch, 'answer', 8)
                    output, free_codes = generate(vq, gen, prefix)
                    add_metrics(aggregate['free'], metrics(output, batch, target))
                    for row, predicted in zip(batch, output):
                        text, valid = decode(predicted.tolist())
                        predictions.append(dict(method=method, split=split, id=row['id'], output=text, valid_utf8=valid))
                    if start == 0:
                        single, _ = generate(vq, gen, prefix[:1])
                        st_logits, _, st_codes = rollout(vq, gen, prefix)
                        assert torch.equal(single, output[:1]), 'batch size changed greedy output'
                        assert torch.equal(st_codes, free_codes), 'ST hard codes differ'
                        assert torch.equal(st_logits.argmax(-1), output), 'ST decoder differs'
                    admitted = [i for i, row in enumerate(batch) if row['kd_usable']]
                    if not admitted:
                        continue
                    selected = [batch[i] for i in admitted]
                    p, t = prefix[admitted], tensor(selected, 'teacher_target', 8)
                    inputs, codes = training_inputs(vq, gen, t, p)
                    logits = gen(inputs, prefix_pad_mask=p == PAD)
                    forced_codes = logits.argmax(-1)
                    forced_output = vq.decode(forced_codes).argmax(-1)
                    reconstruction = vq.decode(codes).argmax(-1)
                    add_metrics(aggregate['teacher_forced'], metrics(forced_output, selected, t))
                    add_metrics(aggregate['reconstruction'], metrics(reconstruction, selected, t))
                    offset = 0
                    for size, level in zip(LEVELS, aggregate['code_levels']):
                        gold = codes[:, offset:offset+size]
                        level['correct'] += int((forced_codes[:, offset:offset+size] == gold).sum())
                        level['free_correct'] += int((free_codes[admitted, offset:offset+size] == gold).sum())
                        level['total'] += gold.numel()
                        level['ce_sum'] += float(F.cross_entropy(logits[:, offset:offset+size].flatten(0, 1), gold.flatten(), reduction='sum'))
                        offset += size
                    assert time.perf_counter() - wall < 570, 'budget exhausted'
                condition['splits'][split] = aggregate
        if method == 'joint':
            for parameter in vq.decoder.parameters():
                parameter.requires_grad = True
            p = tensor(datasets['train'][:4], 'prompt', 64)
            t = tensor(datasets['train'][:4], 'teacher_target', 8)
            logits, _, _ = rollout(vq, gen, p)
            text_loss = F.cross_entropy(logits.flatten(0, 1), t.flatten())
            text_loss.backward()
            norm = lambda parameters: sum(float(p.grad.square().sum()) for p in parameters if p.grad is not None) ** .5
            condition['text_only_gradients'] = {name: norm(parameters) for name, parameters in [('generator', gen.parameters()), ('decoder', vq.decoder.parameters()), ('encoder', vq.encoder.parameters()), ('codebooks', vq.vq.embeddings.parameters())]}
            assert condition['text_only_gradients']['generator'] > 0
            assert condition['text_only_gradients']['decoder'] > 0
            assert condition['text_only_gradients']['encoder'] == condition['text_only_gradients']['codebooks'] == 0
        condition['wall_seconds'] = time.perf_counter() - method_wall
        result['methods'][method] = condition
        print(method, {split: values['free'] for split, values in condition['splits'].items()}, flush=True)
    assert initial_hashes == verify_frozen()
    stopped.set(); monitor.join()
    result['checks'] = dict(frozen_hashes_unchanged=True, st_matches_official=True, batch1_matches_batch16=True, test_opened=False)
    result['metric_references'] = dict(free='answer exact arithmetic, all rows; teacher_text_exact independently compares teacher_target', teacher_forced='teacher_target, kd_usable only', reconstruction='teacher_target, kd_usable only')
    result['cost'] = dict(wall_seconds=time.perf_counter()-wall, cpu_seconds=time.process_time()-cpu, peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, swap_sampling=memory, threads=2, training_steps=0, train_samples=len(datasets['train']), dev_samples=len(datasets['dev']), prompt_byte_positions=5*(len(datasets['train'])+len(datasets['dev']))*64, output_byte_positions=5*(len(datasets['train'])+len(datasets['dev']))*8)
    (OUT / 'RESULTADOS.json').write_text(json.dumps(result, indent=2)+'\n')
    (OUT / 'PREDICCIONES.json').write_text(json.dumps(predictions, indent=2)+'\n')

if __name__ == '__main__':
    main()
