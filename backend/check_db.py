from app.database import SessionLocal
from app.models import Contact

db = SessionLocal()
failed = db.query(Contact).filter(Contact.status == 'FAILED').all()
scheduled = db.query(Contact).filter(Contact.status == 'SCHEDULED').all()
draft_created = db.query(Contact).filter(Contact.status == 'DRAFT_CREATED').all()

print(f"Scheduled: {len(scheduled)}")
print(f"Draft Created: {len(draft_created)}")
print(f"Failed: {len(failed)}")

print("\n--- Failed contacts ---")
for c in failed[:5]:
    print(f"  {c.id} | {c.email} | {c.error}")

print("\n--- Scheduled (stuck) contacts ---")
for c in scheduled[:5]:
    print(f"  {c.id} | {c.email} | scheduled_time={c.scheduled_time} | attempts={c.attempt_count}")

db.close()
