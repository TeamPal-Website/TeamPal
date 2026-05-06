from httpx import AsyncClient

class TestGetCities:

    async def test_get_cities_empty(self, client: AsyncClient):
        response = await client.get('/cities')
        assert response.status_code == 200
        assert response.json() == []

    async def test_get_cities_returns_list_after_add(self, client: AsyncClient):
        await client.post('/cities', json={'title': 'Москва'})
        response = await client.get('/cities')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['title'] == 'Москва'
        assert 'id' in data[0]

    async def test_get_cities_returns_multiple(self, client: AsyncClient):
        await client.post('/cities', json={'title': 'Москва'})
        await client.post('/cities', json={'title': 'Санкт-Петербург'})
        response = await client.get('/cities')
        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_get_cities_no_auth_required(self, client: AsyncClient):
        response = await client.get('/cities')
        assert response.status_code == 200

class TestGetCity:

    async def test_get_city_by_id(self, client: AsyncClient):
        created = await client.post('/cities', json={'title': 'Томск'})
        city_id = created.json()['data']['id']
        response = await client.get(f'/cities/{city_id}')
        assert response.status_code == 200
        assert response.json() == {'id': city_id, 'title': 'Томск'}

    async def test_get_city_not_found(self, client: AsyncClient):
        response = await client.get('/cities/99999')
        assert response.status_code == 404

class TestCreateCity:

    async def test_create_city_success(self, client: AsyncClient):
        response = await client.post('/cities', json={'title': 'Казань'})
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'OK'
        assert data['data']['title'] == 'Казань'
        assert isinstance(data['data']['id'], int)

    async def test_create_city_id_is_positive(self, client: AsyncClient):
        response = await client.post('/cities', json={'title': 'Новосибирск'})
        assert response.json()['data']['id'] > 0

    async def test_create_city_duplicate_returns_409(self, client: AsyncClient):
        await client.post('/cities', json={'title': 'Москва'})
        response = await client.post('/cities', json={'title': 'Москва'})
        assert response.status_code == 409

    async def test_create_city_empty_title_fails(self, client: AsyncClient):
        response = await client.post('/cities', json={'title': ''})
        assert response.status_code == 422

    async def test_create_city_missing_title_fails(self, client: AsyncClient):
        response = await client.post('/cities', json={})
        assert response.status_code == 422

    async def test_create_city_title_too_long_fails(self, client: AsyncClient):
        response = await client.post('/cities', json={'title': 'А' * 51})
        assert response.status_code == 422

    async def test_create_city_title_max_length_accepted(self, client: AsyncClient):
        response = await client.post('/cities', json={'title': 'А' * 50})
        assert response.status_code == 200

    async def test_created_city_appears_in_get_all(self, client: AsyncClient):
        await client.post('/cities', json={'title': 'Екатеринбург'})
        cities = await client.get('/cities')
        titles = [c['title'] for c in cities.json()]
        assert 'Екатеринбург' in titles

    async def test_created_cities_have_unique_ids(self, client: AsyncClient):
        r1 = await client.post('/cities', json={'title': 'Омск'})
        r2 = await client.post('/cities', json={'title': 'Уфа'})
        assert r1.json()['data']['id'] != r2.json()['data']['id']

class TestDeleteCity:

    async def test_delete_city_success(self, client: AsyncClient):
        created = await client.post('/cities', json={'title': 'Воронеж'})
        city_id = created.json()['data']['id']
        response = await client.delete(f'/cities/{city_id}')
        assert response.status_code == 200
        assert response.json() == {'status': 'OK'}
        get_after = await client.get(f'/cities/{city_id}')
        assert get_after.status_code == 404

    async def test_delete_city_not_found(self, client: AsyncClient):
        response = await client.delete('/cities/99999')
        assert response.status_code == 404

    async def test_delete_city_in_use_returns_409(self, client: AsyncClient, authenticated_client: AsyncClient, city: dict, role_id: int, skill_id: int):
        r = await authenticated_client.post('/resumes', json={'role_type_id': role_id, 'city_id': city['id'], 'about_me': 'Test', 'employment_intent': 'commercial', 'status': 'looking_for_job', 'skill_ids': [skill_id], 'experiences': []})
        assert r.status_code == 200, r.text
        response = await client.delete(f"/cities/{city['id']}")
        assert response.status_code == 409
