from datetime import datetime
def generate(title,branch_id,metrics,causal,anomalies):
 lines=[f"# {title}","",f"Branch: `{branch_id}`",f"Generated: {datetime.utcnow().isoformat()}Z","","## Outcome",""]
 lines += [f"- **{k.replace('_',' ').title()}**: {v}" for k,v in metrics.items()]
 lines += ["","## Causal chain",""]
 lines += [f"{i+1}. {x.replace('_',' ').title()}" for i,x in enumerate(causal)] or ["- No causal events recorded."]
 lines += ["","## Anomalies",""]
 lines += [f"- {a['severity'].upper()}: {a['explanation']}" for a in anomalies] if anomalies else ["- None detected."]
 return "\n".join(lines)
