from pathlib import Path
import re
try:
 from sklearn.feature_extraction.text import TfidfVectorizer
except Exception: TfidfVectorizer=None
class LocalRAG:
 def __init__(self,root): self.root=Path(root);self.docs=[];self.vectorizer=None;self.matrix=None
 def ingest(self):
  self.docs=[]
  for p in self.root.rglob('*'):
   if p.is_file() and p.suffix.lower() in {'.md','.txt'}:
    text=p.read_text(encoding='utf-8',errors='ignore'); self.docs.append({'id':str(p.relative_to(self.root)),'text':text[:20000]})
  if self.docs and TfidfVectorizer:
   self.vectorizer=TfidfVectorizer(stop_words='english');self.matrix=self.vectorizer.fit_transform([d['text'] for d in self.docs])
  return len(self.docs)
 def search(self,q,k=4):
  if not self.docs:self.ingest()
  if not self.docs:return []
  if self.vectorizer is None:return self.docs[:k]
  scores=(self.vectorizer.transform([q])@self.matrix.T).toarray()[0]
  idx=scores.argsort()[::-1][:k]
  return [{'id':self.docs[i]['id'],'score':round(float(scores[i]),4),'text':self.docs[i]['text'][:1200]} for i in idx if scores[i]>0]
