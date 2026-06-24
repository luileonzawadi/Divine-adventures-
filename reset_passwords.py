from app import create_app
from app.extensions import db
from app.models import User

app = create_app()
with app.app_context():
    users = User.query.all()
    for u in users:
        u.set_password('password')
    db.session.commit()
    print('All passwords reset to: password')
    for u in users:
        ok = u.check_password('password')
        print(f'  {u.role:10} | {u.email:30} | valid={ok}')
