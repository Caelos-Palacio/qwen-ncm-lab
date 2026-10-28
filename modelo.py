"""Small official NCM classes; byte front end and reproducible local config."""
import sys,pathlib
R=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(R/'upstream'))
import torch
from omegaconf import OmegaConf
from models.vqvae import VQVAE
from models.next_concept import NextConceptTransformer
PAD=256;LEVELS=[1,2,4,8];SEED=170020

def encode(text,n):
 b=list(text.encode('utf8'))
 if len(b)>n:raise ValueError(f'{len(b)} bytes exceeds {n}')
 return b+[PAD]*(n-len(b))

def decode(row):
 bs=[]
 for i in row:
  if i==PAD:break
  bs.append(i)
 try:return bytes(bs).decode('utf8'),True
 except UnicodeDecodeError:return bytes(bs).decode('utf8',errors='replace'),False

def tokenizer():
 q=OmegaConf.create(dict(clss='multiscale_residual_vector_quantizer',decay=.9,epsilon=1e-5,commitment_cost=.25,restart_threshold=.1,levels=dict(use_manual_levels=True,manual_levels=LEVELS),quant_resi=dict(enabled=True,ratio=.5,share_mode=0),aux=dict(fine_drop=dict(prob=.25,min_keep=1))))
 return VQVAE(in_vocab_size=257,context_length=8,embed_dim=64,vqvae_vocab_size=[64]*4,n_layers=4,vector_quantizer_config=q,compression_factor=1,dropout=0.,enc_layers=1,dec_layers=1,pre_quant_groupnorm=8,pre_quant_norm_type='layer')

def generator(vq):
 cfg=OmegaConf.create(dict(n_embd=128,n_layer=4,n_head=4,bias=True,dropout=.0,vocab_size=[64]*4,attn_pattern='block_diagonal',prefix_len=64,use_rope=True,use_level_encoding=True,use_positional_encoding=True,raw_token_prefix=True,query_level0=True,prefix_pad_token_id=PAD,use_qk_norm=True))
 return NextConceptTransformer(vq,cfg)

def training_inputs(vq,gen,target,prefix,corrupt=False,target_codes=None,prefix_features=None):
 codes=vq.encode(target) if target_codes is None else target_codes
 condition=codes.clone()
 if corrupt:
  mask=torch.rand_like(condition,dtype=torch.float)<.05
  condition[mask]=torch.randint(64,(int(mask.sum()),))
 rest=vq.vq.idx_to_ncm_input(condition)
 first=gen.build_l0_query_input(len(target),rest.dtype)
 x=torch.cat([vq.encoder.wte(prefix) if prefix_features is None else prefix_features,first,rest],dim=1)
 return x,codes

@torch.no_grad()
def generate(vq,gen,prefix):
 codes=gen.generate(None,prefix,temperature=0.,top_k=0,top_p=1.)
 logits=vq.decode(codes)
 return logits.argmax(-1),codes
