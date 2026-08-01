M0-05 provides the side-effect-free `health_ping` task. M1 adds the generic
`reca.execute_job` execution boundary, but registers no M2+ domain handler.

Celery owns delivery and execution mechanics only. PostgreSQL Job and
ProcessingRun records remain business authority; retry is a Job Service command
and Valkey state is regenerable.
Future GROBID, analysis, figure, DOCX and export tasks must call Services,
preserve immutable inputs and use idempotency keys.
