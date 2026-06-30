from sqlalchemy.orm import Session
from app.services.prompt_studio_service import prompt_studio_service


def test_prompt_studio_rendering_and_comparison(db: Session):
    # 1. Create prompt template
    prompt = prompt_studio_service.create_prompt(
        db,
        workspace_id=1,
        name="Review Message Template",
        description="Renders formatting template for code review requests",
        template_text="Hello, please review this Python code: {code_snippet}",
        variables=["code_snippet"],
    )
    assert prompt.name == "Review Message Template"

    # 2. Render prompt substituting variables
    rendered = prompt_studio_service.render_prompt(
        db, prompt_id=prompt.id, inputs={"code_snippet": "def hello(): pass"}
    )
    assert rendered == "Hello, please review this Python code: def hello(): pass"

    # 3. Update prompt (creates version 2)
    prompt_studio_service.update_prompt(
        db,
        prompt_id=prompt.id,
        template_text="Please perform senior review on: {code_snippet}",
        variables=["code_snippet"],
    )

    # 4. Compare prompt version 1 vs 2 side by side
    compare_res = prompt_studio_service.compare_prompts(
        db,
        prompt_id=prompt.id,
        version_a=1,
        version_b=2,
        test_inputs={"code_snippet": "print('test')"},
    )
    assert compare_res is not None
    assert compare_res["version_a"]["rendered"] == "Hello, please review this Python code: print('test')"
    assert compare_res["version_b"]["rendered"] == "Please perform senior review on: print('test')"
    assert compare_res["winner"] == "version_b"
