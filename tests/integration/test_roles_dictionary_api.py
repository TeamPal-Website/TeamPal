from httpx import AsyncClient

class TestListRoles:

    async def test_list_roles_empty(self, client: AsyncClient):
        response = await client.get('/roles_dictionary')
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_roles_returns_list_after_add(self, client: AsyncClient):
        await client.post('/roles_dictionary', json={'name': 'Backend Developer'})
        response = await client.get('/roles_dictionary')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['name'] == 'Backend Developer'
        assert 'id' in data[0]

    async def test_list_roles_returns_multiple(self, client: AsyncClient):
        await client.post('/roles_dictionary', json={'name': 'Backend Developer'})
        await client.post('/roles_dictionary', json={'name': 'Frontend Developer'})
        response = await client.get('/roles_dictionary')
        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_list_roles_no_auth_required(self, client: AsyncClient):
        response = await client.get('/roles_dictionary')
        assert response.status_code == 200

class TestGetRole:

    async def test_get_role_by_id(self, client: AsyncClient):
        created = await client.post('/roles_dictionary', json={'name': 'Designer'})
        role_id = created.json()['data']['id']
        response = await client.get(f'/roles_dictionary/{role_id}')
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == role_id
        assert data['name'] == 'Designer'
        assert 'is_active' in data
        assert 'created_at' in data

    async def test_get_role_not_found(self, client: AsyncClient):
        response = await client.get('/roles_dictionary/99999')
        assert response.status_code == 404

class TestCreateRole:

    async def test_create_role_success(self, client: AsyncClient):
        response = await client.post('/roles_dictionary', json={'name': 'DevOps Engineer'})
        assert response.status_code == 200
        data = response.json()['data']
        assert data['name'] == 'DevOps Engineer'
        assert isinstance(data['id'], int)

    async def test_create_role_id_is_positive(self, client: AsyncClient):
        response = await client.post('/roles_dictionary', json={'name': 'QA Engineer'})
        assert response.json()['data']['id'] > 0

    async def test_create_role_duplicate_returns_409(self, client: AsyncClient):
        await client.post('/roles_dictionary', json={'name': 'Manager'})
        response = await client.post('/roles_dictionary', json={'name': 'Manager'})
        assert response.status_code == 409

    async def test_create_role_empty_title_fails(self, client: AsyncClient):
        response = await client.post('/roles_dictionary', json={'name': ''})
        assert response.status_code == 422

    async def test_create_role_missing_title_fails(self, client: AsyncClient):
        response = await client.post('/roles_dictionary', json={})
        assert response.status_code == 422

    async def test_create_role_title_too_long_fails(self, client: AsyncClient):
        response = await client.post('/roles_dictionary', json={'name': 'А' * 151})
        assert response.status_code == 422

    async def test_create_role_title_max_length_accepted(self, client: AsyncClient):
        response = await client.post('/roles_dictionary', json={'name': 'А' * 150})
        assert response.status_code == 200

    async def test_created_role_appears_in_list(self, client: AsyncClient):
        await client.post('/roles_dictionary', json={'name': 'Product Manager'})
        roles = await client.get('/roles_dictionary')
        names = [r['name'] for r in roles.json()]
        assert 'Product Manager' in names

    async def test_created_roles_have_unique_ids(self, client: AsyncClient):
        r1 = await client.post('/roles_dictionary', json={'name': 'Analyst'})
        r2 = await client.post('/roles_dictionary', json={'name': 'Architect'})
        assert r1.json()['data']['id'] != r2.json()['data']['id']

class TestDeleteRole:

    async def test_delete_role_success(self, client: AsyncClient):
        created = await client.post('/roles_dictionary', json={'name': 'Tester'})
        role_id = created.json()['data']['id']
        response = await client.delete(f'/roles_dictionary/{role_id}')
        assert response.status_code == 200

    async def test_delete_role_removes_from_list(self, client: AsyncClient):
        created = await client.post('/roles_dictionary', json={'name': 'Scrum Master'})
        role_id = created.json()['data']['id']
        await client.delete(f'/roles_dictionary/{role_id}')
        response = await client.get('/roles_dictionary')
        assert len(response.json()) == 0

    async def test_delete_role_not_found(self, client: AsyncClient):
        response = await client.delete('/roles_dictionary/99999')
        assert response.status_code == 404
