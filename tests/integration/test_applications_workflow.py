from httpx import AsyncClient


async def _register(client: AsyncClient, prefix: str) -> str:
    client.cookies.clear()
    credentials = {
        "email": f"{prefix}@example.com",
        "password": "password123",
    }
    response = await client.post("/auth/register", json=credentials)
    assert response.status_code == 200
    response = await client.post("/auth/login", json=credentials)
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth(client: AsyncClient, token: str) -> None:
    client.cookies.clear()
    client.cookies.set("access_token", token)


async def _catalog(client: AsyncClient, suffix: str) -> tuple[int, int]:
    role = await client.post(
        "/roles_dictionary",
        json={"name": f"Backend {suffix}"},
    )
    assert role.status_code == 200
    skill = await client.post("/skills", json={"name": f"Python {suffix}"})
    assert skill.status_code == 200
    return role.json()["data"]["id"], skill.json()["data"]["id"]


async def _project(
    client: AsyncClient,
    token: str,
    role_id: int,
    title: str,
    vacancies_count: int = 1,
) -> tuple[int, list[int]]:
    _auth(client, token)
    payload = {
        "title": title,
        "company_name": "TeamPal",
        "employment_intent": "commercial",
        "description": "Описание проекта",
        "tasks": "Задачи проекта",
        "vacancies": [
            {
                "role_type_id": role_id,
                "experience": "none",
                "work_format": "remote",
                "schedule": "5/2",
                "commitment_level": "full_time",
                "description": "Делать API\n\nЗнать FastAPI",
                "salary_amount": 100000 + idx,
                "salary_type": "monthly",
                "contract_type": "gph",
            }
            for idx in range(vacancies_count)
        ],
    }
    response = await client.post("/projects", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    return data["project"]["id"], [v["id"] for v in data["vacancies"]]


async def _resume(
    client: AsyncClient,
    token: str,
    skill_id: int,
    role_type_id: int,
) -> int:
    _auth(client, token)
    payload = {
        "role_type_id": role_type_id,
        "employment_intent": "commercial",
        "commitment_level": "full_time",
        "work_format": "remote",
        "schedule": "5/2",
        "salary_amount": 120000,
        "salary_type": "monthly",
        "contract_type": "gph",
        "about_me": "Кандидат для workflow",
        "skill_ids": [skill_id],
        "experiences": [],
    }
    response = await client.post("/resumes", json=payload)
    assert response.status_code == 200, response.text
    return response.json()["data"]["resume"]["id"]


async def _apply(
    client: AsyncClient,
    token: str,
    resume_id: int,
    vacancy_id: int,
) -> int:
    _auth(client, token)
    response = await client.post(
        "/applications",
        json={"resume_id": resume_id, "vacancy_id": vacancy_id},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["id"]


async def _my_application(
    client: AsyncClient,
    token: str,
    application_id: int,
) -> dict:
    _auth(client, token)
    response = await client.get("/my_applications")
    assert response.status_code == 200
    for item in response.json():
        if item["id"] == application_id:
            return item
    raise AssertionError("application not found")


class TestApplicationsWorkflow:
    async def test_apply_accept_leave_reopens_slot(self, client: AsyncClient):
        owner = await _register(client, "owner-accept")
        applicant = await _register(client, "applicant-accept")
        role_id, skill_id = await _catalog(client, "accept")
        project_id, vacancies = await _project(client, owner, role_id, "Accept project")
        resume_id = await _resume(client, applicant, skill_id, role_id)

        application_id = await _apply(client, applicant, resume_id, vacancies[0])

        _auth(client, owner)
        response = await client.get(f"/projects/{project_id}/applications")
        assert response.status_code == 200
        assert response.json()[0]["id"] == application_id

        response = await client.post(f"/applications/{application_id}/accept")
        assert response.status_code == 200

        item = await _my_application(client, applicant, application_id)
        assert item["status"] == "accepted"

        _auth(client, applicant)
        response = await client.get(f"/projects/{project_id}")
        assert response.status_code == 200
        vacancy = response.json()["vacancies"][0]
        assert vacancy["is_filled"] is True
        assert vacancy["occupant"]["resume_id"] == resume_id

        response = await client.delete(f"/applications/{application_id}")
        assert response.status_code == 200

        item = await _my_application(client, applicant, application_id)
        assert item["status"] == "cancelled"
        assert item["cancel_reason"] == "user_left"

        _auth(client, applicant)
        response = await client.get("/vacancies")
        assert response.status_code == 200
        assert vacancies[0] in [v["vacancy_id"] for v in response.json()]

    async def test_reject_blocks_same_user_for_same_vacancy(self, client: AsyncClient):
        owner = await _register(client, "owner-reject")
        applicant = await _register(client, "applicant-reject")
        role_id, skill_id = await _catalog(client, "reject")
        _, vacancies = await _project(client, owner, role_id, "Reject project")
        first_resume = await _resume(client, applicant, skill_id, role_id)
        second_resume = await _resume(client, applicant, skill_id, role_id)

        application_id = await _apply(client, applicant, first_resume, vacancies[0])

        _auth(client, owner)
        response = await client.post(f"/applications/{application_id}/reject")
        assert response.status_code == 200

        item = await _my_application(client, applicant, application_id)
        assert item["status"] == "rejected"

        _auth(client, applicant)
        response = await client.post(
            "/applications",
            json={"resume_id": second_resume, "vacancy_id": vacancies[0]},
        )
        assert response.status_code == 409

    async def test_pending_cancel_and_project_paused(self, client: AsyncClient):
        owner = await _register(client, "owner-paused")
        applicant = await _register(client, "applicant-paused")
        role_id, skill_id = await _catalog(client, "paused")
        project_id, vacancies = await _project(client, owner, role_id, "Paused project")
        resume_id = await _resume(client, applicant, skill_id, role_id)
        application_id = await _apply(client, applicant, resume_id, vacancies[0])

        _auth(client, applicant)
        response = await client.delete(f"/applications/{application_id}")
        assert response.status_code == 200
        item = await _my_application(client, applicant, application_id)
        assert item["status"] == "cancelled"
        assert item["cancel_reason"] == "user_withdrawn"

        second_resume = await _resume(client, applicant, skill_id, role_id)
        second_application = await _apply(client, applicant, second_resume, vacancies[0])

        _auth(client, owner)
        response = await client.patch(
            f"/projects/{project_id}",
            json={"status": "paused"},
        )
        assert response.status_code == 200

        item = await _my_application(client, applicant, second_application)
        assert item["status"] == "cancelled"
        assert item["cancel_reason"] == "project_paused"

        _auth(client, applicant)
        response = await client.get("/vacancies")
        assert response.status_code == 200
        assert vacancies[0] not in [v["vacancy_id"] for v in response.json()]

    async def test_delete_project_cancels_pending_and_blocks_occupied_delete(
        self,
        client: AsyncClient,
    ):
        owner = await _register(client, "owner-delete")
        applicant = await _register(client, "applicant-delete")
        role_id, skill_id = await _catalog(client, "delete")
        pending_project, pending_vacancies = await _project(
            client,
            owner,
            role_id,
            "Delete pending project",
        )
        pending_resume = await _resume(client, applicant, skill_id, role_id)
        pending_application = await _apply(
            client,
            applicant,
            pending_resume,
            pending_vacancies[0],
        )

        _auth(client, owner)
        response = await client.delete(f"/projects/{pending_project}")
        assert response.status_code == 200

        item = await _my_application(client, applicant, pending_application)
        assert item["status"] == "cancelled"
        assert item["cancel_reason"] == "project_deleted"

        occupied_project, occupied_vacancies = await _project(
            client,
            owner,
            role_id,
            "Delete occupied project",
        )
        occupied_resume = await _resume(client, applicant, skill_id, role_id)
        occupied_application = await _apply(
            client,
            applicant,
            occupied_resume,
            occupied_vacancies[0],
        )

        _auth(client, owner)
        response = await client.post(f"/applications/{occupied_application}/accept")
        assert response.status_code == 200

        response = await client.delete(f"/projects/{occupied_project}")
        assert response.status_code == 409

    async def test_close_releases_resume_for_new_project(self, client: AsyncClient):
        owner = await _register(client, "owner-close")
        applicant = await _register(client, "applicant-close")
        role_id, skill_id = await _catalog(client, "close")
        first_project, first_vacancies = await _project(
            client,
            owner,
            role_id,
            "Close first project",
        )
        resume_id = await _resume(client, applicant, skill_id, role_id)
        application_id = await _apply(client, applicant, resume_id, first_vacancies[0])

        _auth(client, owner)
        response = await client.post(f"/applications/{application_id}/accept")
        assert response.status_code == 200

        response = await client.post(f"/projects/{first_project}/close")
        assert response.status_code == 200

        _auth(client, applicant)
        response = await client.get(f"/projects/{first_project}")
        assert response.status_code == 200
        assert response.json()["project"]["status"] == "close"

        _, second_vacancies = await _project(
            client,
            owner,
            role_id,
            "Close second project",
        )
        new_application_id = await _apply(
            client,
            applicant,
            resume_id,
            second_vacancies[0],
        )
        item = await _my_application(client, applicant, new_application_id)
        assert item["status"] == "pending"

    async def test_cannot_apply_to_own_project_vacancy(self, client: AsyncClient):
        owner = await _register(client, "owner-ownvac")
        role_id, skill_id = await _catalog(client, "ownvac")
        _, vacancies = await _project(client, owner, role_id, "Own vacancy project")
        resume_id = await _resume(client, owner, skill_id, role_id)

        _auth(client, owner)
        response = await client.post(
            "/applications",
            json={"resume_id": resume_id, "vacancy_id": vacancies[0]},
        )
        assert response.status_code == 400

    async def test_applicant_accepts_employer_invitation(self, client: AsyncClient):
        owner = await _register(client, "owner-invite")
        applicant = await _register(client, "applicant-invite")
        role_id, skill_id = await _catalog(client, "inviteflow")
        _, vacancies = await _project(client, owner, role_id, "Invite-only project")
        resume_id = await _resume(client, applicant, skill_id, role_id)

        _auth(client, owner)
        response = await client.post(
            f"/vacancies/{vacancies[0]}/invite_resume",
            json={"resume_id": resume_id},
        )
        assert response.status_code == 200, response.text
        application_id = response.json()["data"]["id"]

        item = await _my_application(client, applicant, application_id)
        assert item["employer_initiated"] is True

        _auth(client, applicant)
        response = await client.post(f"/applications/{application_id}/accept_invitation")
        assert response.status_code == 200

        item = await _my_application(client, applicant, application_id)
        assert item["status"] == "accepted"
