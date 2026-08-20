# FAQ Knowledge Operations Demo

一个完全脱敏的 FAQ 知识运营 Agent 演示项目，展示从知识库体检、线上 Badcase 策略到问法补全的三阶段闭环。

这个仓库是独立编写的作品集演示，不包含公司代码、客户名称、内部接口、日志、数据集或凭证。检索和优化逻辑使用可复现的本地实现，便于直接运行和面试演示。

## 能力概览

- **运营 Agent**：Plan -> Execute -> Reflection，按风险等级把新增、修改、删除动作分为自动执行和人工审核。
- **混合检索**：BM25 关键词召回 + 确定性哈希向量召回，使用加权 RRF 融合并进行轻量重排。
- **三阶段优化**：知识健康治理、Badcase 策略优化、FAQ 对练补全；每一阶段输出可审计报告。
- **前端控制台**：浏览知识库健康度、模拟检索、运行三阶段优化并查看待审核动作。
- **API**：FastAPI 提供健康检查、检索、优化和 Agent 运行接口。

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8090
```

打开 `http://localhost:8090` 查看前端控制台，API 文档位于 `http://localhost:8090/docs`。

运行测试：

```bash
pytest -q
```

## 目录结构

```text
app/
  agent.py       # Plan-Execute-Reflection 运营 Agent
  models.py      # FAQ、Badcase、动作和报告模型
  optimizer.py   # 三阶段知识优化
  retrieval.py   # BM25、向量召回、RRF 与重排
  main.py        # FastAPI 服务与演示数据
frontend/
  index.html     # 单页控制台
  app.js
  styles.css
tests/
```

## 设计边界

演示仓库刻意不连接外部 LLM、向量数据库或企业系统。`QuestionGenerator`、`Reranker` 和 `ActionExecutor` 都是可替换接口，实际项目可以接入模型、Qdrant/PGVector、人工审核系统和灰度发布平台。
