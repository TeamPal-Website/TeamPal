from datetime import timedelta
from httpx import AsyncClient
from src.services.auth import AuthService

class TestRegister:

    async def test_register_success(self, client: AsyncClient):
        response = await client.post('/auth/register', json={'email': 'newuser@example.com', 'password': 'password123'})
        assert response.status_code == 200
        assert response.json()['status'] == 'OK'

    async def test_register_duplicate_email(self, client: AsyncClient):
        user_data = {'email': 'duplicate@example.com', 'password': 'password123'}
        await client.post('/auth/register', json=user_data)
        response = await client.post('/auth/register', json=user_data)
        assert response.status_code == 409

    async def test_register_invalid_email(self, client: AsyncClient):
        response = await client.post('/auth/register', json={'email': 'not-an-email', 'password': 'password123'})
        assert response.status_code == 422

    async def test_register_short_password(self, client: AsyncClient):
        response = await client.post('/auth/register', json={'email': 'user@example.com', 'password': 'short'})
        assert response.status_code == 422

    async def test_register_empty_body(self, client: AsyncClient):
        response = await client.post('/auth/register', content='{}')
        assert response.status_code == 422

    async def test_register_missing_password(self, client: AsyncClient):
        response = await client.post('/auth/register', json={'email': 'user@example.com'})
        assert response.status_code == 422

    async def test_register_missing_email(self, client: AsyncClient):
        response = await client.post('/auth/register', json={'password': 'password123'})
        assert response.status_code == 422

    async def test_register_password_exactly_8(self, client: AsyncClient):
        response = await client.post('/auth/register', json={'email': 'borderline@example.com', 'password': '12345678'})
        assert response.status_code == 200

class TestLogin:

    async def test_login_success(self, client: AsyncClient, registered_user: dict):
        response = await client.post('/auth/login', json=registered_user)
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert len(data['access_token']) > 0

    async def test_login_sets_cookie(self, client: AsyncClient, registered_user: dict):
        response = await client.post('/auth/login', json=registered_user)
        assert 'access_token' in response.cookies

    async def test_login_wrong_password(self, client: AsyncClient, registered_user: dict):
        response = await client.post('/auth/login', json={'email': registered_user['email'], 'password': 'wrongpassword123'})
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        response = await client.post('/auth/login', json={'email': 'ghost@example.com', 'password': 'password123'})
        assert response.status_code == 401

    async def test_login_blocked_user(self, client: AsyncClient):
        admin = {'email': 'admin@example.com', 'password': 'adminpass123'}
        victim = {'email': 'victim@example.com', 'password': 'victimpass123'}
        await client.post('/auth/register', json=admin)
        await client.post('/auth/verify-email', json={'email': admin['email'], 'code': '000000'})
        await client.post('/auth/register', json=victim)
        await client.post('/auth/verify-email', json={'email': victim['email'], 'code': '000000'})
        login_resp = await client.post('/auth/login', json=admin)
        client.cookies.set('access_token', login_resp.json()['access_token'])
        me_resp = await client.get('/auth/me')
        admin_id = me_resp.json()['id']
        victim_id = 2 if admin_id == 1 else 1
        await client.post('/admins/block', json={'user_id': victim_id})
        client.cookies.clear()
        response = await client.post('/auth/login', json=victim)
        assert response.status_code == 403

    async def test_login_returns_valid_jwt(self, client: AsyncClient, registered_user: dict):
        response = await client.post('/auth/login', json=registered_user)
        token = response.json()['access_token']
        decoded = AuthService().decode_token(token)
        assert 'user_id' in decoded
        assert isinstance(decoded['user_id'], int)

class TestGetMe:

    async def test_get_me_authenticated(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get('/auth/me')
        assert response.status_code == 200
        data = response.json()
        assert 'id' in data
        assert data['email'] == 'test@example.com'
        assert 'is_active' in data
        assert 'hashed_password' not in data

    async def test_get_me_no_token(self, client: AsyncClient):
        response = await client.get('/auth/me')
        assert response.status_code == 401

    async def test_get_me_invalid_token(self, client: AsyncClient):
        client.cookies.set('access_token', 'garbage-token-value')
        response = await client.get('/auth/me')
        assert response.status_code == 401

    async def test_get_me_expired_token(self, client: AsyncClient):
        expired_token = AuthService().create_access_token({'user_id': 1}, expires_delta=timedelta(seconds=-10))
        client.cookies.set('access_token', expired_token)
        response = await client.get('/auth/me')
        assert response.status_code == 401

    async def test_get_me_token_without_user_id(self, client: AsyncClient):
        token = AuthService().create_access_token({'some_other_field': 'value'})
        client.cookies.set('access_token', token)
        response = await client.get('/auth/me')
        assert response.status_code == 401

class TestLogout:

    async def test_logout_success(self, authenticated_client: AsyncClient):
        response = await authenticated_client.post('/auth/logout')
        assert response.status_code == 200
        assert response.json() == {'status': 'OK'}

    async def test_logout_without_login(self, client: AsyncClient):
        response = await client.post('/auth/logout')
        assert response.status_code == 200

    async def test_after_logout_me_fails(self, authenticated_client: AsyncClient):
        me_before = await authenticated_client.get('/auth/me')
        assert me_before.status_code == 200
        await authenticated_client.post('/auth/logout')
        authenticated_client.cookies.clear()
        me_after = await authenticated_client.get('/auth/me')
        assert me_after.status_code == 401

class TestChangePassword:

    async def test_change_password_success(self, authenticated_client: AsyncClient, registered_user: dict):
        r = await authenticated_client.post('/auth/change_password', json={'old_password': registered_user['password'], 'new_password': 'newpass999'})
        assert r.status_code == 200
        assert r.json() == {'status': 'OK'}
        await authenticated_client.post('/auth/logout')
        authenticated_client.cookies.clear()
        bad = await authenticated_client.post('/auth/login', json={'email': registered_user['email'], 'password': registered_user['password']})
        assert bad.status_code == 401
        ok = await authenticated_client.post('/auth/login', json={'email': registered_user['email'], 'password': 'newpass999'})
        assert ok.status_code == 200

    async def test_change_password_wrong_old(self, authenticated_client: AsyncClient):
        r = await authenticated_client.post('/auth/change_password', json={'old_password': 'wrong-old-pass-xxx', 'new_password': 'another888'})
        assert r.status_code == 401

    async def test_change_password_requires_auth(self, client: AsyncClient):
        r = await client.post('/auth/change_password', json={'old_password': 'x', 'new_password': '12345678'})
        assert r.status_code == 401
