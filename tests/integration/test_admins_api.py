from httpx import AsyncClient

async def setup_admin_and_target(client: AsyncClient):
    admin_data = {'email': 'admin@example.com', 'password': 'adminpass123'}
    target_data = {'email': 'target@example.com', 'password': 'targetpass123'}
    await client.post('/auth/register', json=admin_data)
    await client.post('/auth/register', json=target_data)
    login_resp = await client.post('/auth/login', json=admin_data)
    token = login_resp.json()['access_token']
    client.cookies.set('access_token', token)
    me_resp = await client.get('/auth/me')
    admin_id = me_resp.json()['id']
    target_id = 2 if admin_id == 1 else 1
    return (admin_data, target_data, target_id)

class TestBlockUser:

    async def test_block_user_success(self, client: AsyncClient):
        _, _, target_id = await setup_admin_and_target(client)
        response = await client.post('/admins/block', json={'user_id': target_id})
        assert response.status_code == 200
        assert response.json() == {'status': 'OK'}

    async def test_block_user_prevents_login(self, client: AsyncClient):
        _, target_data, target_id = await setup_admin_and_target(client)
        await client.post('/admins/block', json={'user_id': target_id})
        client.cookies.clear()
        response = await client.post('/auth/login', json=target_data)
        assert response.status_code == 403

    async def test_block_nonexistent_user(self, client: AsyncClient):
        await setup_admin_and_target(client)
        response = await client.post('/admins/block', json={'user_id': 99999})
        assert response.status_code == 404

    async def test_block_without_auth(self, client: AsyncClient):
        response = await client.post('/admins/block', json={'user_id': 1})
        assert response.status_code == 401

    async def test_block_missing_user_id(self, client: AsyncClient):
        await setup_admin_and_target(client)
        response = await client.post('/admins/block', json={})
        assert response.status_code == 422

class TestUnblockUser:

    async def test_unblock_user_success(self, client: AsyncClient):
        _, _, target_id = await setup_admin_and_target(client)
        await client.post('/admins/block', json={'user_id': target_id})
        response = await client.post('/admins/unblock', json={'user_id': target_id})
        assert response.status_code == 200
        assert response.json() == {'status': 'OK'}

    async def test_unblock_allows_login(self, client: AsyncClient):
        _, target_data, target_id = await setup_admin_and_target(client)
        await client.post('/admins/block', json={'user_id': target_id})
        await client.post('/admins/unblock', json={'user_id': target_id})
        client.cookies.clear()
        response = await client.post('/auth/login', json=target_data)
        assert response.status_code == 200

    async def test_unblock_nonexistent_user(self, client: AsyncClient):
        await setup_admin_and_target(client)
        response = await client.post('/admins/unblock', json={'user_id': 99999})
        assert response.status_code == 404

    async def test_unblock_without_auth(self, client: AsyncClient):
        response = await client.post('/admins/unblock', json={'user_id': 1})
        assert response.status_code == 401

    async def test_unblock_missing_user_id(self, client: AsyncClient):
        await setup_admin_and_target(client)
        response = await client.post('/admins/unblock', json={})
        assert response.status_code == 422
