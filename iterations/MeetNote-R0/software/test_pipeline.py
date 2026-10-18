import unittest,tempfile,os
from pathlib import Path
from dataclasses import replace
from pipeline import *
from cryptography.exceptions import InvalidTag
class PipelineTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.key=os.urandom(32);self.ctx=CaptureContext(str(uuid.uuid4()),str(uuid.uuid4()),'consent-1',True,'key-ref-1');self.data=b'\x00\x01'*16000;self.blob=seal(self.data,self.ctx,0,0,16000,self.key)
 def tearDown(self):self.tmp.cleanup()
 def test_roundtrip_timeline(self):
  h,d=unseal(self.blob,self.key);self.assertEqual(d,self.data);self.assertEqual(h['sample_count'],16000);self.assertEqual(h['boot_id'],self.ctx.boot_id)
 def test_no_consent_or_permit(self):
  for ctx in [replace(self.ctx,physical_permit=False),replace(self.ctx,consent_event_id='')]:
   with self.assertRaises(PermissionError):seal(self.data,ctx,0,0,16000,self.key)
 def test_tamper_ciphertext(self):
  tampered=self.blob[:-1]+bytes([self.blob[-1]^1])
  with self.assertRaises(InvalidTag):unseal(tampered,self.key)
 def test_tamper_evidence_header(self):
  altered=self.blob.replace(b'consent-1',b'consent-2')
  with self.assertRaises(InvalidTag):unseal(altered,self.key)
 def test_wrong_key(self):
  with self.assertRaises(InvalidTag):unseal(self.blob,os.urandom(32))
 def test_atomic_encrypted_spool(self):
  p=self.root/'chunk.mn';atomic_save(p,self.blob);self.assertEqual(p.read_bytes(),self.blob);self.assertFalse(p.with_suffix('.mn.partial').exists())
 def test_resume_after_server_recreation(self):
  s=UploadStore(self.root);u=s.create(sha(self.blob),len(self.blob));s.append(u,0,self.blob[:1234]);s=UploadStore(self.root);self.assertEqual(s.offset(u),1234);s.append(u,1234,self.blob[1234:]);self.assertEqual(s.finish(u),sha(self.blob));self.assertEqual(s.finish(u),sha(self.blob))
 def test_exact_retry_and_conflict(self):
  s=UploadStore(self.root);u=s.create(sha(self.blob),len(self.blob));s.append(u,0,self.blob[:100]);self.assertEqual(s.append(u,0,self.blob[:100]),100)
  with self.assertRaises(ValueError):s.append(u,0,b'bad')
  with self.assertRaises(ValueError):s.append(u,101,b'bad')
 def test_incomplete_and_digest(self):
  s=UploadStore(self.root);u=s.create(sha(self.blob),len(self.blob));s.append(u,0,b'x')
  with self.assertRaises(ValueError):s.finish(u)
  s.append(u,1,b'x'*(len(self.blob)-1))
  with self.assertRaises(ValueError):s.finish(u)
 def test_confirmation_required(self):
  t=candidate_task('Prepare draft',self.ctx.meeting_id,0,16000,sha(self.blob));self.assertEqual(t['status'],'needs_confirmation');self.assertIsNone(t['assignee']);self.assertIsNone(t['confirmed_by'])
 def test_path_traversal(self):
  with self.assertRaises(ValueError):UploadStore(self.root).offset('../escape')
 def test_length_timeline_mismatch(self):
  with self.assertRaises(ValueError):seal(b'bad',self.ctx,0,0,16000,self.key)
if __name__=='__main__':unittest.main(verbosity=2)
