from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

class TestGetMyProfile:

    async def test_get_my_profile_success(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get('/profiles/me')
        assert response.status_code == 200

    async def test_get_my_profile_no_auth_returns_401(self, client: AsyncClient):
        response = await client.get('/profiles/me')
        assert response.status_code == 401

    async def test_get_my_profile_fields_present(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get('/profiles/me')
        data = response.json()
        assert 'id' in data
        assert 'first_name' in data
        assert 'last_name' in data
        assert 'age' in data
        assert 'gender' in data
        assert 'avatar' in data

    async def test_get_my_profile_no_hashed_password(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get('/profiles/me')
        assert 'hashed_password' not in response.json()

    async def test_get_my_profile_initial_fields_are_none(self, client: AsyncClient, registered_user: dict):
        login = await client.post('/auth/login', json=registered_user)
        assert login.status_code == 200
        client.cookies.set('access_token', login.json()['access_token'])
        response = await client.get('/profiles/me')
        assert response.status_code == 200
        data = response.json()
        assert data['first_name'] is None
        assert data['last_name'] is None
        assert data['age'] is None
        assert data['gender'] is None

    async def test_profile_created_automatically_on_register(self, client: AsyncClient):
        await client.post('/auth/register', json={'email': 'newuser@example.com', 'password': 'password123'})
        login = await client.post('/auth/login', json={'email': 'newuser@example.com', 'password': 'password123'})
        client.cookies.set('access_token', login.json()['access_token'])
        response = await client.get('/profiles/me')
        assert response.status_code == 200

class TestGetProfileByUserId:

    async def test_get_profile_by_user_id_success(self, client: AsyncClient, authenticated_client: AsyncClient, user_id: int):
        response = await client.get(f'/profiles/{user_id}')
        assert response.status_code == 200
        data = response.json()
        assert 'avatar' in data

    async def test_get_profile_no_auth_required(self, client: AsyncClient, authenticated_client: AsyncClient, user_id: int):
        response = await client.get(f'/profiles/{user_id}')
        assert response.status_code == 200

    async def test_get_profile_nonexistent_returns_404(self, client: AsyncClient):
        response = await client.get('/profiles/99999')
        assert response.status_code == 404

    async def test_get_profile_reflects_patch(self, authenticated_client: AsyncClient, user_id: int):
        await authenticated_client.patch('/profiles', json={'first_name': 'Иван'})
        response = await authenticated_client.get(f'/profiles/{user_id}')
        assert response.status_code == 200
        assert response.json()['first_name'] == 'Иван'

class TestPatchProfile:

    async def test_patch_profile_no_auth_returns_401(self, client: AsyncClient):
        response = await client.patch('/profiles', json={'first_name': 'Иван'})
        assert response.status_code == 401

    async def test_patch_profile_success(self, authenticated_client: AsyncClient):
        response = await authenticated_client.patch('/profiles', json={'first_name': 'Иван', 'last_name': 'Петров'})
        assert response.status_code == 200
        assert response.json() == {'status': 'OK'}

    async def test_patch_profile_changes_are_persisted(self, authenticated_client: AsyncClient):
        await authenticated_client.patch('/profiles', json={'first_name': 'Мария'})
        profile = await authenticated_client.get('/profiles/me')
        assert profile.json()['first_name'] == 'Мария'

    async def test_patch_profile_partial_update_preserves_other_fields(self, authenticated_client: AsyncClient):
        await authenticated_client.patch('/profiles', json={'first_name': 'Олег'})
        await authenticated_client.patch('/profiles', json={'last_name': 'Смирнов'})
        profile = await authenticated_client.get('/profiles/me')
        assert profile.json()['first_name'] == 'Олег'
        assert profile.json()['last_name'] == 'Смирнов'

    async def test_patch_profile_age_valid(self, authenticated_client: AsyncClient):
        response = await authenticated_client.patch('/profiles', json={'age': 25})
        assert response.status_code == 200

    async def test_patch_profile_age_below_minimum_fails(self, authenticated_client: AsyncClient):
        response = await authenticated_client.patch('/profiles', json={'age': 15})
        assert response.status_code == 422

    async def test_patch_profile_age_above_maximum_fails(self, authenticated_client: AsyncClient):
        response = await authenticated_client.patch('/profiles', json={'age': 101})
        assert response.status_code == 422

    async def test_patch_profile_age_boundary_16(self, authenticated_client: AsyncClient):
        response = await authenticated_client.patch('/profiles', json={'age': 16})
        assert response.status_code == 200

    async def test_patch_profile_age_boundary_100(self, authenticated_client: AsyncClient):
        response = await authenticated_client.patch('/profiles', json={'age': 100})
        assert response.status_code == 200

    async def test_patch_profile_gender_male(self, authenticated_client: AsyncClient):
        response = await authenticated_client.patch('/profiles', json={'gender': 'male'})
        assert response.status_code == 200

    async def test_patch_profile_gender_female(self, authenticated_client: AsyncClient):
        response = await authenticated_client.patch('/profiles', json={'gender': 'female'})
        assert response.status_code == 200

    async def test_patch_profile_invalid_gender_fails(self, authenticated_client: AsyncClient):
        response = await authenticated_client.patch('/profiles', json={'gender': 'alien'})
        assert response.status_code == 422

    async def test_patch_profile_name_whitespace_stripped(self, authenticated_client: AsyncClient):
        await authenticated_client.patch('/profiles', json={'first_name': '  Анна  '})
        profile = await authenticated_client.get('/profiles/me')
        assert profile.json()['first_name'] == 'Анна'

    async def test_patch_profile_name_only_spaces_fails(self, authenticated_client: AsyncClient):
        response = await authenticated_client.patch('/profiles', json={'first_name': '   '})
        assert response.status_code == 422

    async def test_patch_profile_first_name_too_long_fails(self, authenticated_client: AsyncClient):
        response = await authenticated_client.patch('/profiles', json={'first_name': 'А' * 36})
        assert response.status_code == 422

    async def test_patch_profile_empty_body_succeeds(self, authenticated_client: AsyncClient):
        r1 = await authenticated_client.patch('/profiles', json={'first_name': 'Патч'})
        assert r1.status_code == 200
        r2 = await authenticated_client.patch('/profiles', json={'first_name': 'Патч'})
        assert r2.status_code == 200

    async def test_patch_profile_with_contacts(self, authenticated_client: AsyncClient):
        contacts = {'phone': '+79991234567', 'telegram': '@ivan', 'github': 'ivan-dev'}
        response = await authenticated_client.patch('/profiles', json={'contacts': contacts})
        assert response.status_code == 200

    async def test_patch_profile_contacts_persisted(self, authenticated_client: AsyncClient):
        contacts = {'phone': '+79991234567', 'telegram': '@ivan', 'github': None}
        await authenticated_client.patch('/profiles', json={'contacts': contacts})
        profile = await authenticated_client.get('/profiles/me')
        saved = profile.json()['contacts']
        assert saved['phone'] == '+79991234567'
        assert saved['telegram'] == '@ivan'

class TestAvatarUpload:

    async def test_upload_avatar_requires_auth(self, client: AsyncClient):
        with patch('src.services.profiles.is_object_storage_configured', return_value=True):
            response = await client.post('/profiles/me/avatar', files={'file': ('t.png', b'\x89PNG\r\n\x1a\n', 'image/png')})
        assert response.status_code == 401

    async def test_upload_avatar_503_when_storage_not_configured(self, authenticated_client: AsyncClient):
        with patch('src.services.profiles.is_object_storage_configured', return_value=False):
            response = await authenticated_client.post('/profiles/me/avatar', files={'file': ('t.png', b'x', 'image/png')})
        assert response.status_code == 503

    @patch('src.services.profiles.delete_avatar_key', new_callable=AsyncMock)
    @patch('src.services.profiles.upload_avatar', new_callable=AsyncMock)
    @patch('src.services.profiles.is_object_storage_configured', return_value=True)
    async def test_upload_avatar_persists_key_and_returns_proxy_path(self, _configured, mock_upload, mock_delete, authenticated_client: AsyncClient):
        mock_upload.return_value = 'avatars/1/a1b2c3d4e5f6.jpg'
        response = await authenticated_client.post('/profiles/me/avatar', files={'file': ('t.png', b'x', 'image/png')})
        assert response.status_code == 200
        body = response.json()
        mock_upload.assert_awaited_once()
        me_user = await authenticated_client.get('/auth/me')
        uid = me_user.json()['id']
        expected = f'/profiles/{uid}/avatar/file'
        assert body['avatar'] == expected
        me = await authenticated_client.get('/profiles/me')
        assert me.json()['avatar'] == expected

    async def test_get_my_avatar_file_requires_auth(self, client: AsyncClient):
        response = await client.get('/profiles/me/avatar/file')
        assert response.status_code == 401

    @patch('src.services.profiles.get_object_bytes', new_callable=AsyncMock)
    @patch('src.services.profiles.delete_avatar_key', new_callable=AsyncMock)
    @patch('src.services.profiles.upload_avatar', new_callable=AsyncMock)
    @patch('src.services.profiles.is_object_storage_configured', return_value=True)
    async def test_get_my_avatar_file_streams_bytes(self, _configured, mock_upload, mock_delete, mock_get_bytes, authenticated_client: AsyncClient):
        mock_upload.return_value = 'avatars/1/stream.jpg'
        mock_get_bytes.return_value = (b'\xff\xd8\xff', 'image/jpeg')
        up = await authenticated_client.post('/profiles/me/avatar', files={'file': ('t.png', b'x', 'image/png')})
        assert up.status_code == 200
        response = await authenticated_client.get('/profiles/me/avatar/file')
        assert response.status_code == 200
        assert response.content == b'\xff\xd8\xff'
        assert response.headers.get('content-type', '').startswith('image/jpeg')

    @patch('src.services.profiles.get_object_bytes', new_callable=AsyncMock)
    @patch('src.services.profiles.delete_avatar_key', new_callable=AsyncMock)
    @patch('src.services.profiles.upload_avatar', new_callable=AsyncMock)
    @patch('src.services.profiles.is_object_storage_configured', return_value=True)
    async def test_get_user_avatar_file_streams_without_auth(self, _configured, mock_upload, mock_delete, mock_get_bytes, client: AsyncClient, authenticated_client: AsyncClient):
        mock_upload.return_value = 'avatars/1/byuserid.jpg'
        mock_get_bytes.return_value = (b'\xff\xd8\xff', 'image/jpeg')
        up = await authenticated_client.post('/profiles/me/avatar', files={'file': ('t.png', b'x', 'image/png')})
        assert up.status_code == 200
        uid = (await authenticated_client.get('/auth/me')).json()['id']
        response = await client.get(f'/profiles/{uid}/avatar/file')
        assert response.status_code == 200
        assert response.content == b'\xff\xd8\xff'

    @patch('src.services.profiles.get_object_bytes', new_callable=AsyncMock)
    @patch('src.services.profiles.delete_avatar_key', new_callable=AsyncMock)
    @patch('src.services.profiles.upload_avatar', new_callable=AsyncMock)
    @patch('src.services.profiles.is_object_storage_configured', return_value=True)
    async def test_get_my_avatar_file_404_when_missing_in_storage(self, _configured, mock_upload, mock_delete, mock_get_bytes, authenticated_client: AsyncClient):
        mock_upload.return_value = 'avatars/1/miss.jpg'
        up = await authenticated_client.post('/profiles/me/avatar', files={'file': ('t.png', b'x', 'image/png')})
        assert up.status_code == 200
        mock_get_bytes.return_value = None
        response = await authenticated_client.get('/profiles/me/avatar/file')
        assert response.status_code == 404
