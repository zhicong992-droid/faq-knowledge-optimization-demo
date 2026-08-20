from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .agent import KnowledgeOperationsAgent
from .models import Badcase, FAQ
from .optimizer import ThreeStageOptimizer
from .retrieval import HybridRetriever


DEMO_FAQS = [
    FAQ("faq-001", "账户服务", "如何修改登录密码？", "在安全设置中选择修改密码，完成身份验证后保存新密码。", ("忘记密码怎么改？", "登录密码在哪里修改？")),
    FAQ("faq-002", "账户服务", "如何绑定新的手机号码？", "在账户安全页面验证原手机号后绑定新手机号。", ("换手机号后怎么更新？",)),
    FAQ("faq-003", "费用与账单", "如何下载本月账单？", "进入账单页面选择月份并点击下载，即可获得 PDF 账单。", ("本月账单在哪里导出？", "怎么保存账单？")),
    FAQ("faq-004", "费用与账单", "账单金额有误怎么办？", "请在账单详情提交复核申请，并附上相关交易信息。", ("发现扣费不对怎么处理？",)),
    FAQ("faq-005", "售后服务", "如何申请人工客服？", "在帮助中心选择在线客服，输入人工客服即可转接。", ("怎么转人工？",)),
]


app = FastAPI(title="FAQ Knowledge Operations Demo", version="1.0.0")
app.mount("/static", StaticFiles(directory=Path(__file__).parent.parent / "frontend"), name="static")


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=10)


class OptimizeRequest(BaseModel):
    badcases: list[Badcase] = Field(default_factory=list)


def build_agent() -> KnowledgeOperationsAgent:
    return KnowledgeOperationsAgent(ThreeStageOptimizer(DEMO_FAQS))


@app.get("/", response_class=FileResponse)
def index() -> Path:
    return Path(__file__).parent.parent / "frontend" / "index.html"


@app.get("/api/health")
def health() -> dict:
    report = ThreeStageOptimizer(DEMO_FAQS).run()
    return {"status": "ok", "metrics": report.metrics, "finding_count": len(report.health_findings)}


@app.post("/api/search")
def search(request: SearchRequest) -> dict:
    hits = HybridRetriever(DEMO_FAQS).search(request.query, request.top_k)
    return {"query": request.query, "hits": [hit.__dict__ for hit in hits]}


@app.post("/api/optimize")
def optimize(request: OptimizeRequest) -> dict:
    return ThreeStageOptimizer(DEMO_FAQS).run(request.badcases).to_dict()


@app.post("/api/agent/run")
def run_agent(request: OptimizeRequest) -> dict:
    return build_agent().run(request.badcases).to_dict()
