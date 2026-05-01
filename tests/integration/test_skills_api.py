from httpx import AsyncClient


class TestListSkills:

    async def test_list_skills_empty(self, client: AsyncClient):
        response = await client.get("/skills")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_skills_returns_list_after_add(self, client: AsyncClient):
        await client.post("/skills", json={"name": "Python"})
        response = await client.get("/skills")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Python"
        assert "id" in data[0]

    async def test_list_skills_returns_multiple(self, client: AsyncClient):
        await client.post("/skills", json={"name": "Python"})
        await client.post("/skills", json={"name": "JavaScript"})
        response = await client.get("/skills")
        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_list_skills_no_auth_required(self, client: AsyncClient):
        response = await client.get("/skills")
        assert response.status_code == 200


class TestGetSkill:

    async def test_get_skill_by_id(self, client: AsyncClient):
        created = await client.post("/skills", json={"name": "Go"})
        skill_id = created.json()["data"]["id"]
        response = await client.get(f"/skills/{skill_id}")
        assert response.status_code == 200
        assert response.json() == {"id": skill_id, "name": "Go"}

    async def test_get_skill_not_found(self, client: AsyncClient):
        response = await client.get("/skills/99999")
        assert response.status_code == 404


class TestCreateSkill:

    async def test_create_skill_success(self, client: AsyncClient):
        response = await client.post("/skills", json={"name": "Rust"})
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["name"] == "Rust"
        assert isinstance(data["id"], int)

    async def test_create_skill_id_is_positive(self, client: AsyncClient):
        response = await client.post("/skills", json={"name": "TypeScript"})
        assert response.json()["data"]["id"] > 0

    async def test_create_skill_duplicate_returns_409(self, client: AsyncClient):
        await client.post("/skills", json={"name": "Python"})
        response = await client.post("/skills", json={"name": "Python"})
        assert response.status_code == 409

    async def test_create_skill_empty_title_fails(self, client: AsyncClient):
        response = await client.post("/skills", json={"name": ""})
        assert response.status_code == 422

    async def test_create_skill_missing_title_fails(self, client: AsyncClient):
        response = await client.post("/skills", json={})
        assert response.status_code == 422

    async def test_create_skill_title_too_long_fails(self, client: AsyncClient):
        response = await client.post("/skills", json={"name": "А" * 256})
        assert response.status_code == 422

    async def test_create_skill_title_max_length_accepted(self, client: AsyncClient):
        response = await client.post("/skills", json={"name": "А" * 255})
        assert response.status_code == 200

    async def test_created_skill_appears_in_list(self, client: AsyncClient):
        await client.post("/skills", json={"name": "Elixir"})
        skills = await client.get("/skills")
        titles = [s["name"] for s in skills.json()]
        assert "Elixir" in titles

    async def test_created_skills_have_unique_ids(self, client: AsyncClient):
        r1 = await client.post("/skills", json={"name": "Scala"})
        r2 = await client.post("/skills", json={"name": "Kotlin"})
        assert r1.json()["data"]["id"] != r2.json()["data"]["id"]


class TestDeleteSkill:

    async def test_delete_skill_success(self, client: AsyncClient):
        created = await client.post("/skills", json={"name": "Swift"})
        skill_id = created.json()["data"]["id"]
        response = await client.delete(f"/skills/{skill_id}")
        assert response.status_code == 200

    async def test_delete_skill_removes_from_list(self, client: AsyncClient):
        created = await client.post("/skills", json={"name": "Ruby"})
        skill_id = created.json()["data"]["id"]
        await client.delete(f"/skills/{skill_id}")
        
        response = await client.get("/skills")
        assert len(response.json()) == 0

    async def test_delete_skill_not_found(self, client: AsyncClient):
        response = await client.delete("/skills/99999")
        assert response.status_code == 404