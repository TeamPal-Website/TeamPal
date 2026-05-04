from pydantic import BaseModel, ConfigDict, Field

class ResumeSkill(BaseModel):
    id: int
    resume_id: int
    skill_id: int
    model_config = ConfigDict(from_attributes=True)

class ResumeSkillCreate(BaseModel):
    skill_id: int = Field(gt=0)

class ResumeSkillPatch(BaseModel):
    skill_id: int = Field(ge=1)

class ResumeSkillAdd(BaseModel):
    resume_id: int = Field(gt=0)
    skill_id: int = Field(gt=0)
