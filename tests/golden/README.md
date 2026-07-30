# Golden test fixtures

本目录保留经人工核验、版本固定的确定性与 Agent 合同测试材料；禁止把模型即时输出直接当作黄金答案。

后续按里程碑创建下列子目录：

```text
agent_router/       # 模糊主题、前置条件、阶段路由
prompt_injection/   # 不可信 PDF/用户内容不能改变权限
claim_audit/        # 证据缺失、数字、因果、修订漂移
degradation/        # Provider 失败与用户可见的降级披露
```

每个 fixture 需附带版本、输入来源 ID（可使用合成或获授权材料）、预期 finding/路由/降级状态及人工审核依据。不得在该目录放入受版权保护论文全文、真实敏感数据或有效密钥。
