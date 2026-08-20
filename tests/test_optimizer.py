from app.models import Badcase, FAQ
from app.optimizer import ThreeStageOptimizer


def test_three_stage_optimizer_reports_health_badcase_and_expansion():
    faqs = [
        FAQ("a", "账户", "如何修改登录密码？", "在安全设置中修改。", ()),
        FAQ("b", "账户", "如何修改登录密码？", "请联系人工客服。", ("密码怎么改？",)),
    ]

    report = ThreeStageOptimizer(faqs).run([Badcase("忘记密码怎么改？", "a")])

    assert any(item.finding_type == "duplicate_faq" for item in report.health_findings)
    assert report.badcase_actions[0].payload["question"] == "忘记密码怎么改？"
    assert report.expansion_actions
