"""Executable protocol reference. No microphone, radio, ASR or hardware driver.
Requires cryptography. Keys are supplied by caller, never embedded in artifacts.
"""
from dataclasses import dataclass
from pathlib import Path
import hashlib,json,os,struct,uuid
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
MAGIC=b'MN01'
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def sha(x):return hashlib.sha256(x).hexdigest()
@dataclass(frozen=True)
class CaptureContext:
    meeting_id:str
    boot_id:str
    consent_event_id:str
    physical_permit:bool
    key_id:str

def seal(data:bytes,ctx:CaptureContext,seq:int,start_sample:int,sample_count:int,key:bytes):
    if not ctx.physical_permit or not ctx.consent_event_id:
        raise PermissionError('Recording requires consent and physical permit')
    if len(key)!=32 or min(seq,start_sample,sample_count)<0:
        raise ValueError('Invalid key or timeline')
    # A fresh per-meeting DEK plus 96-bit random nonce; production must bound invocation count.
    nonce=os.urandom(12)
    header={'version':1,'meeting_id':ctx.meeting_id,'boot_id':ctx.boot_id,'consent_event_id':ctx.consent_event_id,'key_id':ctx.key_id,'sequence':seq,'start_sample':start_sample,'sample_count':sample_count,'sample_rate':16000,'channels':1,'format':'pcm_s16le','nonce':nonce.hex()}
    if len(data)!=sample_count*2:raise ValueError('PCM byte count differs from timeline')
    aad=canonical(header)
    return MAGIC+struct.pack('>I',len(aad))+aad+AESGCM(key).encrypt(nonce,data,aad)
def unseal(blob,key):
    if blob[:4]!=MAGIC or len(blob)<8:raise ValueError('Bad format')
    n=struct.unpack('>I',blob[4:8])[0]
    if n>16384 or 8+n+16>len(blob):raise ValueError('Invalid header size')
    aad=blob[8:8+n];h=json.loads(aad)
    data=AESGCM(key).decrypt(bytes.fromhex(h['nonce']),blob[8+n:],aad)
    return h,data

def atomic_save(path:Path,data:bytes):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.partial')
    fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(temp,path)
        d=os.open(path.parent,os.O_RDONLY)
        try:os.fsync(d)
        finally:os.close(d)
    finally:
        if temp.exists():temp.unlink()

class UploadStore:
    """Local single-writer mock of resumable server, not a network service.
    Persistent manifest, append-only partial, digest-checked finalization.
    """
    def __init__(self,root:Path):self.root=root;root.mkdir(parents=True,exist_ok=True)
    def _dir(self,upload_id):
        uuid.UUID(upload_id) # prevents filesystem traversal
        return self.root/upload_id
    def create(self,expected_sha,size):
        if len(expected_sha)!=64 or any(c not in '0123456789abcdef' for c in expected_sha) or not 0<size<=32*1024*1024:raise ValueError('Invalid upload contract')
        uid=str(uuid.uuid4());d=self._dir(uid);d.mkdir()
        atomic_save(d/'manifest.json',canonical({'sha256':expected_sha,'size':size}))
        return uid
    def offset(self,uid):
        d=self._dir(uid)
        for name in ['complete.bin','data.partial']:
            if (d/name).exists():return (d/name).stat().st_size
        return 0
    def append(self,uid,offset,data):
        d=self._dir(uid);m=json.loads((d/'manifest.json').read_text());current=self.offset(uid)
        p=d/('complete.bin' if (d/'complete.bin').exists() else 'data.partial')
        if offset<current and offset+len(data)<=current:
            with p.open('rb') as f:f.seek(offset);old=f.read(len(data))
            if old==data:return current # exactly identical retry only
        if offset!=current or (d/'complete.bin').exists():raise ValueError('409 offset conflict')
        if current+len(data)>m['size']:raise ValueError('413 declared size exceeded')
        fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
        with os.fdopen(fd,'ab') as f:f.write(data);f.flush();os.fsync(f.fileno())
        return current+len(data)
    def finish(self,uid):
        d=self._dir(uid);m=json.loads((d/'manifest.json').read_text())
        if (d/'complete.bin').exists():return m['sha256']
        p=d/'data.partial'
        if not p.exists() or p.stat().st_size!=m['size']:raise ValueError('Incomplete')
        if sha(p.read_bytes())!=m['sha256']:raise ValueError('Digest mismatch; discard/quarantine upload')
        os.replace(p,d/'complete.bin')
        fd=os.open(d,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
        return m['sha256']

def candidate_task(text,meeting_id,start_sample,end_sample,chunk_sha):
    if end_sample<=start_sample:raise ValueError('Missing evidence interval')
    return {'text':text,'meeting_id':meeting_id,'status':'needs_confirmation','assignee':None,'due_at':None,'evidence':[{'start_sample':start_sample,'end_sample':end_sample,'sample_rate':16000,'chunk_sha256':chunk_sha}], 'confirmed_by':None}
