# Repository Integration Tests

本目录承载数据库、对象存储、Celery/Valkey、GROBID、Provider、统计/图表、引用处理器和 Agent runtime 与 RECA Service 的真实协作测试。

每个实际引入项目应覆盖固定版本、兼容性、失败/降级、资源边界、输出转换、`project_id` 隔离和实现元数据记录。在线服务只保留少量 Smoke；required CI 使用可追溯 Recorded/离线材料，不能用随机 Mock 冒充真实集成。
