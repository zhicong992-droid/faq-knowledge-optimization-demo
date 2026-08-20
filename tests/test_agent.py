from app.agent import KnowledgeOperationsAgent
from app.models import Badcase, FAQ
from app.optimizer import ThreeStageOptimizer


def test_agent_emits_auditable_steps_and_routes_actions():
    optimizer = ThreeStageOptimizer([
        FAQ("a", "账户", "如何修改登录密码？", "在安全设置中修改。", ()),
    ])

    run = KnowledgeOperationsAgent(optimizer).run([Badcase("忘记密码怎么改？", "a")])

    assert [step.name for step in run.steps] == ["plan", "execute", "reflection"]
    assert run.actions
    assert run.reflection["auto_executable_count"] == len(run.actions)
