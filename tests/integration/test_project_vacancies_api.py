from httpx import AsyncClient


async def setup_project_with_vacancy(client: AsyncClient):
    """Создает пользователя, проект и вакансию для тестов."""
    user_data = {"email": "vacancy_owner@example.com", "password": "password123"}
    await client.post("/auth/register", json=user_data)
    
    login_resp = await client.post("/auth/login", json=user_data)
    token = login_resp.json()["access_token"]
    client.cookies.set("access_token", token)
    
    role_resp = await client.post("/roles_dictionary", json={"name": "Developer"})
    role_id = role_resp.json()["data"]["id"]
    
    project_resp = await client.post("/projects", json={
        "title": "Test Project",
        "company_name": "Test Company",
        "description": "Description",
        "tasks": "Tasks",
        "status": "active",
        "employment_intent": "commercial",
        "vacancies": [{"role_type_id": role_id, "description": "Need developer"}],
    })
    project_id = project_resp.json()["data"]["project"]["id"]
    vacancy_id = project_resp.json()["data"]["vacancies"][0]["id"]
    
    return user_data, project_id, vacancy_id, role_id


class TestListProjectVacancies:

    async def test_list_vacancies_empty(self, authenticated_client: AsyncClient):
        role_resp = await authenticated_client.post("/roles_dictionary", json={"name": "Backend"})
        role_id = role_resp.json()["data"]["id"]
        
        project_resp = await authenticated_client.post("/projects", json={
            "title": "Empty Project",
            "company_name": "Company",
            "description": "Desc",
            "tasks": "Tasks",
            "status": "active",
            "employment_intent": "commercial",
            "vacancies": [{"role_type_id": role_id, "description": "Test"}],
        })
        project_id = project_resp.json()["data"]["project"]["id"]
        vacancy_id = project_resp.json()["data"]["vacancies"][0]["id"]
        
        response = await authenticated_client.get(f"/projects/{project_id}/vacancies")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == vacancy_id

    async def test_list_vacancies_returns_vacancies(self, authenticated_client: AsyncClient):
        _, project_id, vacancy_id, _ = await setup_project_with_vacancy(authenticated_client)
        
        response = await authenticated_client.get(f"/projects/{project_id}/vacancies")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == vacancy_id

    async def test_list_vacancies_project_not_found(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get("/projects/99999/vacancies")
        assert response.status_code == 404

    async def test_list_vacancies_no_auth_returns_401(self, client: AsyncClient):
        response = await client.get("/projects/1/vacancies")
        assert response.status_code == 401


class TestCreateProjectVacancy:

    async def test_create_vacancy_success(self, authenticated_client: AsyncClient):
        role_resp = await authenticated_client.post("/roles_dictionary", json={"name": "Frontend"})
        role_id = role_resp.json()["data"]["id"]
        
        project_resp = await authenticated_client.post("/projects", json={
            "title": "Project for Vacancy",
            "company_name": "Company",
            "description": "Desc",
            "tasks": "Tasks",
            "status": "active",
            "employment_intent": "commercial",
            "vacancies": [{"role_type_id": role_id, "description": "Initial"}],
        })
        project_id = project_resp.json()["data"]["project"]["id"]
        
        response = await authenticated_client.post(f"/projects/{project_id}/vacancies", json={
            "role_type_id": role_id,
            "description": "Looking for frontend developer",
        })
        assert response.status_code == 200

    async def test_create_vacancy_invalid_role(self, authenticated_client: AsyncClient):
        role_resp = await authenticated_client.post("/roles_dictionary", json={"name": "Dev"})
        role_id = role_resp.json()["data"]["id"]
        
        project_resp = await authenticated_client.post("/projects", json={
            "title": "Project",
            "company_name": "Company",
            "description": "Desc",
            "tasks": "Tasks",
            "status": "active",
            "employment_intent": "commercial",
            "vacancies": [{"role_type_id": role_id, "description": "Test"}],
        })
        project_id = project_resp.json()["data"]["project"]["id"]
        
        response = await authenticated_client.post(f"/projects/{project_id}/vacancies", json={
            "role_type_id": 99999,
            "description": "Invalid role",
        })
        assert response.status_code == 404

    async def test_create_vacancy_project_not_found(self, authenticated_client: AsyncClient):
        response = await authenticated_client.post("/projects/99999/vacancies", json={
            "role_type_id": 1,
            "description": "Test",
        })
        assert response.status_code == 404

    async def test_create_vacancy_exceeds_limit(self, authenticated_client: AsyncClient):
        role_resp = await authenticated_client.post("/roles_dictionary", json={"name": "Dev"})
        role_id = role_resp.json()["data"]["id"]
        
        project_resp = await authenticated_client.post("/projects", json={
            "title": "Project with many vacancies",
            "company_name": "Company",
            "description": "Desc",
            "tasks": "Tasks",
            "status": "active",
            "employment_intent": "commercial",
            "vacancies": [{"role_type_id": role_id, "description": "Initial"}],
        })
        project_id = project_resp.json()["data"]["project"]["id"]
        
        for i in range(10):
            await authenticated_client.post(f"/projects/{project_id}/vacancies", json={
                "role_type_id": role_id,
                "description": f"Vacancy {i}",
            })
        
        response = await authenticated_client.post(f"/projects/{project_id}/vacancies", json={
            "role_type_id": role_id,
            "description": "Extra vacancy",
        })
        assert response.status_code == 409

    async def test_create_vacancy_no_auth_returns_401(self, client: AsyncClient):
        response = await client.post("/projects/1/vacancies", json={
            "role_type_id": 1,
            "description": "Test",
        })
        assert response.status_code == 401


class TestUpdateProjectVacancy:

    async def test_update_vacancy_success(self, authenticated_client: AsyncClient):
        _, project_id, vacancy_id, _ = await setup_project_with_vacancy(authenticated_client)
        
        response = await authenticated_client.patch(
            f"/projects/{project_id}/vacancies/{vacancy_id}",
            json={"description": "Updated description"}
        )
        assert response.status_code == 200

    async def test_update_vacancy_not_found(self, authenticated_client: AsyncClient):
        _, project_id, _, _ = await setup_project_with_vacancy(authenticated_client)
        
        response = await authenticated_client.patch(
            f"/projects/{project_id}/vacancies/99999",
            json={"description": "Updated"}
        )
        assert response.status_code == 404

    async def test_update_vacancy_project_not_found(self, authenticated_client: AsyncClient):
        response = await authenticated_client.patch(
            "/projects/99999/vacancies/1",
            json={"description": "Updated"}
        )
        assert response.status_code == 404

    async def test_update_vacancy_no_auth_returns_401(self, client: AsyncClient):
        response = await client.patch("/projects/1/vacancies/1", json={
            "description": "Updated"
        })
        assert response.status_code == 401


class TestDeleteProjectVacancy:

    async def test_delete_vacancy_success(self, authenticated_client: AsyncClient):
        _, project_id, vacancy_id, _ = await setup_project_with_vacancy(authenticated_client)
        
        response = await authenticated_client.delete(
            f"/projects/{project_id}/vacancies/{vacancy_id}"
        )
        assert response.status_code == 200

    async def test_delete_vacancy_removes_from_list(self, authenticated_client: AsyncClient):
        _, project_id, vacancy_id, _ = await setup_project_with_vacancy(authenticated_client)
        
        await authenticated_client.delete(f"/projects/{project_id}/vacancies/{vacancy_id}")
        
        response = await authenticated_client.get(f"/projects/{project_id}/vacancies")
        assert len(response.json()) == 0

    async def test_delete_vacancy_not_found(self, authenticated_client: AsyncClient):
        _, project_id, _, _ = await setup_project_with_vacancy(authenticated_client)
        
        response = await authenticated_client.delete(
            f"/projects/{project_id}/vacancies/99999"
        )
        assert response.status_code == 404

    async def test_delete_vacancy_project_not_found(self, authenticated_client: AsyncClient):
        response = await authenticated_client.delete("/projects/99999/vacancies/1")
        assert response.status_code == 404

    async def test_delete_vacancy_no_auth_returns_401(self, client: AsyncClient):
        response = await client.delete("/projects/1/vacancies/1")
        assert response.status_code == 401