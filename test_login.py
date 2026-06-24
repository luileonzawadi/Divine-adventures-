from app import create_app
import re

app = create_app()
client = app.test_client()

with app.app_context():
    # Step 1: GET the login page to grab a CSRF token
    r = client.get('/login')
    print('GET /login status:', r.status_code)
    html = r.data.decode()
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    csrf = match.group(1) if match else ''
    print('CSRF token found:', bool(csrf))

    # Step 2: POST login with email + password
    r2 = client.post('/login', data={
        'email': 'admin@devine.com',
        'password': 'password',
        'csrf_token': csrf
    }, follow_redirects=False)
    print('POST /login status:', r2.status_code)
    print('Redirect Location:', r2.headers.get('Location', 'none'))
    body = r2.data.decode()
    if 'Invalid email or password' in body:
        print('RESULT: Login FAILED - bad credentials message shown')
    elif r2.status_code in (301, 302):
        print('RESULT: Login SUCCEEDED - redirected to', r2.headers.get('Location'))
    else:
        print('RESULT: Unexpected response')
        print(body[:500])
