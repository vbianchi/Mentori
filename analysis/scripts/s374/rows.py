import json,os
# files.FILES is not imported here: rows uses none of it, and importing files globs the upstream results (D155).
def walk(o):
    if isinstance(o,dict):
        if 'question_id' in o or 'item_key' in o: yield o; return
        for v in o.values(): yield from walk(v)
    elif isinstance(o,list):
        for v in o: yield from walk(v)
def load_rows(path):
    if path.endswith('.jsonl'):
        rows=[]; 
        for l in open(path):
            j=json.loads(l)
            if '_header' in j: continue
            rows.append(j)
        return None,rows
    d=json.load(open(path))
    return d,list(walk(d))
def qid(r):
    q=r.get('question_id')
    if q: return q
    k=r.get('item_key','')
    return k.rsplit('_',1)[0]
def answer(r):
    g=r.get('generation')
    if isinstance(g,dict) and isinstance(g.get('answer'),str): return _unwrap(g['answer'])
    for k in ('answer','final_answer','generated_answer','response'):
        if isinstance(r.get(k),str): return _unwrap(r[k])
    return None
def _unwrap(s):
    """The llama3:8b depth-sweep file stores each answer as the text of a GenerationResult repr
    ("GenerationResult(answer='...', latency_s=..., gen_model=..., error=...)"); return its answer field,
    and None when that field is empty (a failed generation, e.g. "Maximum turns (1) reached").
    Found 9 October (phase-3 worklist F10): until then the judge was sent the whole repr."""
    if not s.startswith('GenerationResult('): return s
    import ast
    try:
        call=ast.parse(s,mode='eval').body
        for kw in call.keywords:
            if kw.arg=='answer':
                v=ast.literal_eval(kw.value)
                return v if isinstance(v,str) and v.strip() else None
    except (SyntaxError,ValueError):
        pass
    raise ValueError('unparseable GenerationResult repr: '+s[:120])
def error(r):
    g=r.get('generation')
    if isinstance(g,dict) and 'error' in g: return g.get('error')
    return r.get('error')
def genmodel(r,d,path):
    g=r.get('generation') if isinstance(r.get('generation'),dict) else {}
    for v in (g.get('gen_model'), r.get('gen_model'), r.get('model_id'), r.get('model')):
        if v: return v
    if isinstance(d,dict):
        for k in ('gen_model','model'):
            if d.get(k): return d[k]
    if 'S314' in path: return 'gemini::gemini-3-flash-preview (from header)'
    return None
