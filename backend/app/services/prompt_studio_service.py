import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.studio_models import PromptTemplate, PromptVersion


class PromptStudioService:
    def create_prompt(
        self, db: Session, *, workspace_id: int, name: str, description: Optional[str] = None, template_text: str, variables: Optional[List[str]] = None
    ) -> PromptTemplate:
        prompt = PromptTemplate(
            workspace_id=workspace_id,
            name=name,
            description=description,
            template_text=template_text,
            variables=json.dumps(variables or []),
        )
        db.add(prompt)
        db.commit()
        db.refresh(prompt)

        # Save version 1
        ver = PromptVersion(
            prompt_id=prompt.id,
            version=1,
            template_text=template_text,
        )
        db.add(ver)
        db.commit()

        return prompt

    def get_prompts(self, db: Session, workspace_id: int) -> List[PromptTemplate]:
        return db.query(PromptTemplate).filter(PromptTemplate.workspace_id == workspace_id).all()

    def get_prompt(self, db: Session, prompt_id: int) -> Optional[PromptTemplate]:
        return db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()

    def update_prompt(
        self, db: Session, *, prompt_id: int, template_text: str, variables: Optional[List[str]] = None
    ) -> PromptTemplate:
        prompt = self.get_prompt(db, prompt_id)
        if not prompt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt template not found.")

        prompt.template_text = template_text
        if variables is not None:
            prompt.variables = json.dumps(variables)
        db.commit()

        # Version increment
        latest = (
            db.query(PromptVersion)
            .filter(PromptVersion.prompt_id == prompt_id)
            .order_by(PromptVersion.version.desc())
            .first()
        )
        next_ver = (latest.version + 1) if latest else 1

        ver = PromptVersion(
            prompt_id=prompt_id,
            version=next_ver,
            template_text=template_text,
        )
        db.add(ver)
        db.commit()

        db.refresh(prompt)
        return prompt

    def render_prompt(self, db: Session, *, prompt_id: int, inputs: Dict[str, Any]) -> str:
        prompt = self.get_prompt(db, prompt_id)
        if not prompt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt template not found.")

        rendered = prompt.template_text
        for key, val in inputs.items():
            rendered = rendered.replace(f"{{{key}}}", str(val))
        return rendered

    def compare_prompts(
        self, db: Session, *, prompt_id: int, version_a: int, version_b: int, test_inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Renders two different versions of a prompt side by side and returns compared layouts.
        """
        ver_a = (
            db.query(PromptVersion)
            .filter(PromptVersion.prompt_id == prompt_id, PromptVersion.version == version_a)
            .first()
        )
        ver_b = (
            db.query(PromptVersion)
            .filter(PromptVersion.prompt_id == prompt_id, PromptVersion.version == version_b)
            .first()
        )

        if not ver_a or not ver_b:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt versions not found.")

        rendered_a = ver_a.template_text
        rendered_b = ver_b.template_text
        for k, v in test_inputs.items():
            rendered_a = rendered_a.replace(f"{{{k}}}", str(v))
            rendered_b = rendered_b.replace(f"{{{k}}}", str(v))

        # Mock comparisons scores for semantic check
        return {
            "version_a": {
                "version": version_a,
                "rendered": rendered_a,
                "readability_score": 85.0,
                "cost_est": 0.002,
            },
            "version_b": {
                "version": version_b,
                "rendered": rendered_b,
                "readability_score": 92.0,
                "cost_est": 0.0025,
            },
            "winner": "version_b",
        }


prompt_studio_service = PromptStudioService()
