from httpx import AsyncClient


async def setup_profile_with_project(client: AsyncClient):
    """Создает пользователя, профиль и проект для тестов."""
    user_data = {"email": "project_owner@example.com", "password": "password123"}
    await client.post("/auth/register", json=user_data)
    
    login_resp = await client.post("/auth/login", json=user_data)
    token = login_resp.json()["access_token"]
    client.cookies.set("access_token", token)
    
    me_resp = await client.get("/auth/me")
    user_id = me_resp.json()["id"]
    
    return user_data, user_id


class TestGetProfileProjects:

    async def test_get_profile_projects_empty(self, client: AsyncClient):
        await setup_profile_with_project(client)
        response = await client.get("/profiles/1/projects")
        assert response.status_code == 200
        assert response.json() == []

    async def test_get_profile_projects_not_found(self, client: AsyncClient):
        response = await client.get("/profiles/99999/projects")
        assert response.status_code == 404

    async def test_get_profile_projects_no_auth_required(self, client: AsyncClient):
        await setup_profile_with_project(client)
        response = await client.get("/profiles/1/projects")
        assert response.status_code == 200


class TestGetProject:

    async def test_get_project_not_found_profile(self, client: AsyncClient):
        response = await client.get("/profiles/99999/projects/1")
        assert response.status_code == 401

    async def test_get_project_not_found_project(self, client: AsyncClient):
        await setup_profile_with_project(client)
        response = await client.get("/profiles/1/projects/99999")
        assert response.status_code == 404

    async def test_get_project_no_vacancies(self, client: AsyncClient):
        await setup_profile_with_project(client)
        response = await client.get("/profiles/1/projects/1")
        assert response.status_code == 404


class TestGetMyProjects:

    async def test_get_my_projects_empty(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get("/my_projects")
        assert response.status_code == 200
        assert response.json() == []

    async def test_get_my_projects_no_auth_returns_401(self, client: AsyncClient):
        response = await client.get("/my_projects")
        assert response.status_code == 401


class TestGetMyProject:

    async def test_get_my_project_not_found(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get("/my_project/99999")
        assert response.status_code == 404

    async def test_get_my_project_no_auth_returns_401(self, client: AsyncClient):
        response = await client.get("/my_project/1")
        assert response.status_code == 401


class TestSearchProjects:

    async def test_search_projects_empty(self, client: AsyncClient):
        response = await client.get("/projects")
        assert response.status_code == 200
        assert response.json() == []

    async def test_search_projects_with_query(self, client: AsyncClient):
        response = await client.get("/projects?q=test")
        assert response.status_code == 200

    async def test_search_projects_with_pagination(self, client: AsyncClient):
        response = await client.get("/projects?page=1&per_page=10")
        assert response.status_code == 200

    async def test_search_projects_with_filters(self, client: AsyncClient):
        response = await client.get("/projects?city_id=1&employment_intent=commercial")
        assert response.status_code == 200


class TestCreateProject:

    async def test_create_project_no_auth_returns_401(self, client: AsyncClient):
        response = await client.post("/projects", json={
            "title": "Test Project",
            "company_name": "Test Company",
            "description": "Description",
            "tasks": "Tasks",
            "status": "active",
            "employment_intent": "commercial",
            "vacancies": [{"role_type_id": 1, "description": "Test"}],
        })
        assert response.status_code == 401

    async def test_create_project_success(self, authenticated_client: AsyncClient, role_id: int):
        response = await authenticated_client.post("/projects", json={
            "title": "Test Project",
            "company_name": "Test Company",
            "description": "Description",
            "tasks": "Tasks",
            "status": "active",
            "employment_intent": "commercial",
            "vacancies": [{"role_type_id": role_id, "description": "Need developer"}],
        })
        assert response.status_code == 200

    async def test_create_project_with_vacancies(self, authenticated_client: AsyncClient, role_id: int):
        response = await authenticated_client.post("/projects", json={
            "title": "Project with Vacancy",
            "company_name": "Company",
            "description": "Desc",
            "tasks": "Tasks",
            "status": "active",
            "employment_intent": "commercial",
            "vacancies": [
                {"role_type_id": role_id, "description": "Need developer"}
            ],
        })
        assert response.status_code == 200

    async def test_create_project_invalid_city(self, authenticated_client: AsyncClient):
        response = await authenticated_client.post("/projects", json={
            "title": "Project",
            "company_name": "Company",
            "description": "Desc",
            "tasks": "Tasks",
            "status": "active",
            "employment_intent": "commercial",
            "city_id": 99999,
            "vacancies": [{"role_type_id": 1, "description": "Test"}],
        })
        assert response.status_code == 404

    async def test_create_project_invalid_role(self, authenticated_client: AsyncClient):
        response = await authenticated_client.post("/projects", json={
            "title": "Project",
            "company_name": "Company",
            "description": "Desc",
            "tasks": "Tasks",
            "status": "active",
            "employment_intent": "commercial",
            "vacancies": [
                {"role_type_id": 99999, "description": "Need developer"}
            ],
        })
        assert response.status_code == 404

    async def test_create_project_exceeds_limit(self, authenticated_client: AsyncClient, role_id: int):
        for i in range(10):
            await authenticated_client.post("/projects", json={
                "title": f"Project {i}",
                "company_name": "Company",
                "description": "Desc",
                "tasks": "Tasks",
                "status": "active",
                "employment_intent": "commercial",
                "vacancies": [{"role_type_id": role_id, "description": "Test"}],
            })
        
        response = await authenticated_client.post("/projects", json={
            "title": "Extra Project",
            "company_name": "Company",
            "description": "Desc",
            "tasks": "Tasks",
            "status": "active",
            "employment_intent": "commercial",
            "vacancies": [{"role_type_id": 1, "description": "Test"}],
        })
        assert response.status_code == 409


class TestPatchProject:

    async def test_patch_project_no_auth_returns_401(self, client: AsyncClient):
        response = await client.patch("/projects/1", json={"title": "New Title"})
        assert response.status_code == 401

    async def test_patch_project_not_found(self, authenticated_client: AsyncClient):
        response = await authenticated_client.patch("/projects/99999", json={"title": "New Title"})
        assert response.status_code == 404


class TestDeleteProject:

    async def test_delete_project_no_auth_returns_401(self, client: AsyncClient):
        response = await client.delete("/projects/1")
        assert response.status_code == 401

    async def test_delete_project_not_found(self, authenticated_client: AsyncClient):
        response = await authenticated_client.delete("/projects/99999")
        assert response.status_code == 404