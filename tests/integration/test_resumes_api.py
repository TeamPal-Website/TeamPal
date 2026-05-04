from httpx import AsyncClient


async def setup_profile_with_resume(client: AsyncClient):
    """Создает пользователя и профиль для тестов резюме."""
    user_data = {"email": "resume_owner@example.com", "password": "password123"}
    await client.post("/auth/register", json=user_data)
    
    login_resp = await client.post("/auth/login", json=user_data)
    token = login_resp.json()["access_token"]
    client.cookies.set("access_token", token)
    
    me_resp = await client.get("/auth/me")
    user_id = me_resp.json()["id"]
    
    return user_data, user_id


class TestGetProfileResumes:

    async def test_get_profile_resumes_empty(self, client: AsyncClient):
        await setup_profile_with_resume(client)
        response = await client.get("/profiles/1/resumes")
        assert response.status_code == 200
        assert response.json() == []

    async def test_get_profile_resumes_not_found(self, client: AsyncClient):
        response = await client.get("/profiles/99999/resumes")
        assert response.status_code == 404

    async def test_get_profile_resumes_no_auth_required(self, client: AsyncClient):
        await setup_profile_with_resume(client)
        response = await client.get("/profiles/1/resumes")
        assert response.status_code == 200


class TestGetResume:

    async def test_get_resume_not_found_profile(self, client: AsyncClient):
        response = await client.get("/profiles/99999/resumes/1")
        assert response.status_code == 404

    async def test_get_resume_not_found_resume(self, client: AsyncClient):
        await setup_profile_with_resume(client)
        response = await client.get("/profiles/1/resumes/99999")
        assert response.status_code == 404

    async def test_get_resume_no_skills(self, client: AsyncClient):
        await setup_profile_with_resume(client)
        response = await client.get("/profiles/1/resumes/1")
        assert response.status_code == 404


class TestGetMyResumes:

    async def test_get_my_resumes_empty(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get("/my_resumes")
        assert response.status_code == 200
        assert response.json() == []

    async def test_get_my_resumes_no_auth_returns_401(self, client: AsyncClient):
        response = await client.get("/my_resumes")
        assert response.status_code == 401


class TestGetMyResume:

    async def test_get_my_resume_not_found(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get("/my_resume/99999")
        assert response.status_code == 404

    async def test_get_my_resume_no_auth_returns_401(self, client: AsyncClient):
        response = await client.get("/my_resume/1")
        assert response.status_code == 401


class TestSearchResumes:

    async def test_search_resumes_empty(self, client: AsyncClient):
        response = await client.get("/resumes")
        assert response.status_code == 200
        assert response.json() == []

    async def test_search_resumes_with_query(self, client: AsyncClient):
        response = await client.get("/resumes?q=python")
        assert response.status_code == 200

    async def test_search_resumes_with_pagination(self, client: AsyncClient):
        response = await client.get("/resumes?page=1&per_page=10")
        assert response.status_code == 200

    async def test_search_resumes_with_filters(self, client: AsyncClient):
        response = await client.get("/resumes?city_id=1&employment_intent=commercial")
        assert response.status_code == 200

    async def test_search_resumes_with_skill_ids(self, client: AsyncClient, skill_id: int):
        response = await client.get(
            "/resumes",
            params=[("skill_ids", str(skill_id)), ("skill_ids", str(skill_id))],
        )
        assert response.status_code == 200

    async def test_search_resumes_skill_id_with_skill_ids_merges(self, client: AsyncClient, skill_id: int):
        response = await client.get(f"/resumes?skill_id={skill_id}&skill_ids={skill_id}")
        assert response.status_code == 200

    async def test_search_resumes_skill_ids_max_length(self, client: AsyncClient):
        qs = "&".join([f"skill_ids={i}" for i in range(1, 28)])
        response = await client.get(f"/resumes?{qs}")
        assert response.status_code == 422


class TestCreateResume:

    async def test_create_resume_no_auth_returns_401(self, client: AsyncClient):
        response = await client.post("/resumes", json={
            "role_type_id": 1,
            "about_me": "Experienced developer",
            "employment_intent": "commercial",
            "status": "looking_for_job",
            "skill_ids": [1],
            "experiences": [],
        })
        assert response.status_code == 401

    async def test_create_resume_success(self, authenticated_client: AsyncClient, skill_id: int, role_id: int):
        response = await authenticated_client.post("/resumes", json={
            "role_type_id": role_id,
            "about_me": "Experienced developer",
            "employment_intent": "commercial",
            "status": "looking_for_job",
            "skill_ids": [skill_id],
            "experiences": [],
        })
        print(f"DEBUG: {response.status_code} - {response.json()}")
        assert response.status_code == 200

    async def test_create_resume_with_skills(self, authenticated_client: AsyncClient, skill_id: int, role_id: int):
        response = await authenticated_client.post("/resumes", json={
            "role_type_id": role_id,
            "about_me": "Desc",
            "employment_intent": "commercial",
            "status": "looking_for_job",
            "skill_ids": [skill_id],
            "experiences": [],
        })
        assert response.status_code == 200

    async def test_create_resume_with_experiences(self, authenticated_client: AsyncClient, skill_id: int, role_id: int):
        response = await authenticated_client.post("/resumes", json={
            "role_type_id": role_id,
            "about_me": "Desc",
            "employment_intent": "commercial",
            "status": "looking_for_job",
            "skill_ids": [skill_id],
            "experiences": [
                {
                    "company_name": "Tech Corp",
                    "role_type_id": role_id,
                    "start_date": "2020-01-01",
                    "end_date": "2023-01-01",
                    "description": "Worked on projects",
                }
            ],
        })
        print(f"DEBUG: {response.status_code} - {response.json()}")
        assert response.status_code == 200

    async def test_create_resume_exceeds_limit(self, authenticated_client: AsyncClient, skill_id: int, role_id: int):
        for i in range(5):
            await authenticated_client.post("/resumes", json={
                "role_type_id": role_id,
                "about_me": "Desc",
                "employment_intent": "commercial",
                "status": "looking_for_job",
                "skill_ids": [skill_id],
                "experiences": [],
            })
        
        response = await authenticated_client.post("/resumes", json={
            "role_type_id": role_id,
            "about_me": "Desc",
            "employment_intent": "commercial",
            "status": "looking_for_job",
            "skill_ids": [skill_id],
            "experiences": [],
        })
        assert response.status_code == 409


class TestPatchResume:

    async def test_patch_resume_no_auth_returns_401(self, client: AsyncClient):
        response = await client.patch("/resumes/1", json={"title": "New Title"})
        assert response.status_code == 401

    async def test_patch_resume_not_found(self, authenticated_client: AsyncClient):
        response = await authenticated_client.patch("/resumes/99999", json={"title": "New Title"})
        assert response.status_code == 404


class TestDeleteResume:

    async def test_delete_resume_no_auth_returns_401(self, client: AsyncClient):
        response = await client.delete("/resumes/1")
        assert response.status_code == 401

    async def test_delete_resume_not_found(self, authenticated_client: AsyncClient):
        response = await authenticated_client.delete("/resumes/99999")
        assert response.status_code == 404