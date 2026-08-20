from app.models import FAQ
from app.retrieval import HybridRetriever


def test_hybrid_retrieval_returns_both_channels_for_exact_question():
    faqs = [
        FAQ("a", "账户", "如何修改登录密码？", "在安全设置中修改。", ("忘记密码怎么改？",)),
        FAQ("b", "账单", "如何下载账单？", "在账单页面下载。", ()),
    ]

    hits = HybridRetriever(faqs).search("忘记密码怎么改？", top_k=1)

    assert hits[0].faq_id == "a"
    assert set(hits[0].channels) == {"bm25", "dense"}
