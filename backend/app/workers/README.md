M0-05 provides a single Celery worker and the side-effect-free `health_ping`
task. Formal asynchronous research jobs are deliberately deferred to M1.

Celery owns delivery, retry and execution mechanics only. PostgreSQL Job and
ProcessingRun records remain business authority; Valkey state is regenerable.
Future GROBID, analysis, figure, DOCX and export tasks must call Services,
preserve immutable inputs and use idempotency keys.
