"""Debug: find actual web pages and emails that contain injection content."""
import sys, json
sys.path.insert(0, ".")

from pathlib import Path
from aicomp_sdk.agents import build_agent
from aicomp_sdk.guardrails.optimal import Guardrail as OptimalGuardrail
from aicomp_sdk.core.env.sandbox import SandboxEnv
from aicomp_sdk.core.predicates import eval_predicates

fixtures = Path("aicomp_sdk/fixtures")

# Check web pages with injection content
data = json.load(open("aicomp_sdk/fixtures/web_corpus.json"))
pages = data["pages"]
inj_phrases = ["ignore previous", "forget", "disregard", "overlook",
               "you must", "immediately", "execute", "required", "mandatory",
               "system mode", "admin override", "step 1", "1."]
count = 0
for p in pages:
    c = (p.get("content", "") or "").lower()
    if any(phrase in c for phrase in inj_phrases):
        count += 1
        if count <= 10:
            print(f"WEB INJECTION: id={p['id']} content={p.get('content','')[:200]}")
print(f"Total web pages with injection: {count}")

# Check emails
mail = json.load(open("aicomp_sdk/fixtures/mail_seed.json"))
print(f"\nMail structure type: {type(mail)}")
if isinstance(mail, dict):
    print(f"Mail keys: {list(mail.keys())[:10]}")
    for folder, msgs in mail.items():
        if isinstance(msgs, list):
            print(f"\nFolder '{folder}': {len(msgs)} messages")
            for m in msgs[:5]:
                mid = m.get("id", "?")
                subj = m.get("subject", "?")
                body = (m.get("body", "") or "")[:100]
                print(f"  {mid}: {subj} | body={body}")
elif isinstance(mail, list):
    print(f"Mail is a list with {len(mail)} items")
    for m in mail[:5]:
        print(f"  {m.get('id','?')}: {m.get('subject','?')}")

# Check for injection in emails
print("\n\nEmails with injection content:")
email_count = 0
def check_emails(msgs):
    global email_count
    for m in msgs:
        body = (m.get("body", "") or "").lower()
        content = (m.get("content", "") or "").lower()
        text = body + content
        if any(phrase in text for phrase in inj_phrases):
            email_count += 1
            if email_count <= 10:
                print(f"  EMAIL INJECTION: id={m.get('id','?')} body={text[:200]}")

if isinstance(mail, dict):
    for folder, msgs in mail.items():
        if isinstance(msgs, list):
            check_emails(msgs)
elif isinstance(mail, list):
    check_emails(mail)
print(f"Total emails with injection: {email_count}")

# Now test with actual web search
env = SandboxEnv(seed=123, fixtures_dir=fixtures, agent=build_agent("deterministic"), guardrail=OptimalGuardrail())
env.reset()
result = env.interact("search demo", max_tool_hops=1)
trace = env.export_trace_dict()
for e in trace["tool_events"]:
    if e.get("ok"):
        print(f"\nSearch results for 'demo': {e.get('output','')[:500]}")
