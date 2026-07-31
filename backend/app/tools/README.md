# Controlled tools

Separate deterministic domain tools from Agent Tool wrappers. Deterministic
tools perform approved parsing, validation, statistics, rendering and checks;
Agent wrappers expose only existing whitelist names and Schemas and delegate to
Services. They do not execute arbitrary Python/Shell/SQL or call third-party
SDKs directly. M0 introduces no formal research Tool.
