# Golden test fixtures

本目录还承载第三方科研能力的固定效果基准，包括 GROBID 版式/页码、PaperQA 候选证据、ASReview 排序建议、Pandera FailureCase、SciPy/statsmodels 数值、Matplotlib 输出、引用格式和 Agents SDK/ARS 契约材料。

复用或改造上游 fixture、测试结构和预期结果时，必须保留项目、仓库、Commit、许可证、原路径和修改记录；许可证受限内容不得因“仅用于测试”而省略归属或复制审查。

本目录保留经人工核验、版本固定的确定性与 Agent 合同测试材料；禁止把模型即时输出直接当作黄金答案。

后续按里程碑创建下列子目录：

```text
agent_router/       # 模糊主题、前置条件、阶段路由
prompt_injection/   # 不可信 PDF/用户内容不能改变权限
claim_audit/        # 证据缺失、数字、因果、修订漂移
degradation/        # Provider 失败与用户可见的降级披露
```

每个 fixture 需附带版本、输入来源 ID（可使用合成或获授权材料）、预期 finding/路由/降级状态及人工审核依据。不得在该目录放入受版权保护论文全文、真实敏感数据或有效密钥。
