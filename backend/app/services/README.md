# Application services

Services are the authority for permissions, project isolation, transactions,
state transitions, versioning, approval, provenance, invalidation and audit.
They normalize PyAlex/GROBID/PaperQA/ASReview/Pandera/SciPy/statsmodels/DOCX/
Agent SDK outputs into existing RECA objects.

Routers, Workers, Tools and Agents may invoke Services but may not bypass them.
M0 retains only the authentication and health foundations.
