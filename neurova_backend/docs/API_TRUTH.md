# Neurova API Truth (Single Source of Use) 
## Product-Facing APIs (ONLY THESE SHOULD BE USED) 
All frontend applications, demos, pilots, and integrations MUST use: 
/api/v1/clinical-ops/* 
These APIs encapsulate: - workflow - permissions - audit logging - safety checks 
- regulatory assumptions 
## Internal APIs (DO NOT USE DIRECTLY) 
The following APIs exist for internal service orchestration only: 
/api/v1/orders/ 
/api/v1/sessions/ 
/api/v1/scoring/ 
/api/v1/reports/ 
Calling these directly from frontend or external systems is 
prohibited. 
## Rationale 
This separation ensures: - regulatory safety - stable workflows - reduced misuse - easier audits