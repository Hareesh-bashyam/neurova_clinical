## STAFF / Create Patient
- Endpoint: POST /api/v1/clinical-ops/staff/patients/create
- Auth: Staff JWT
- Called By: Staff Dashboard
- Purpose: Create patient record
- Success: 201 { patient_id }
- Errors: 400, 403

## STAFF / Create Order
- Endpoint: POST /api/v1/clinical-ops/staff/orders/create
- Auth: Staff JWT
- Called By: Staff Dashboard
- Purpose: Create patient order and assign battery
- Success: 201 { order_id, public_token }
- Errors: 400, 403

## STAFF / View Clinic Queue
- Endpoint: GET /api/v1/clinical-ops/staff/queue
- Auth: Staff JWT
- Called By: Staff Dashboard
- Purpose: View clinic processing queue
- Success: 200 { orders[] }
- Errors: 403

## PUBLIC / Bootstrap Assessment
- Endpoint: GET /api/v1/clinical-ops/public/order/{token}
- Auth: Public Token
- Called By: Patient Device
- Purpose: Bootstrap public assessment session
- Success: 200 { order, battery }
- Errors: 404, 410

## STAFF / Mark Order Delivered
- Endpoint: POST /api/v1/clinical-ops/staff/orders/deliver
- Auth: Staff JWT
- Called By: Staff Dashboard
- Purpose: Set delivery details and mark order delivered
- Success: 200 { status }
- Errors: 400, 403

## STAFF / Export Order JSON
- Endpoint: GET /api/v1/clinical-ops/staff/order/{order_id}/export
- Auth: Staff JWT
- Called By: Staff Dashboard
- Purpose: Export order data as JSON
- Success: 200 { order_json }
- Errors: 403, 404

## PUBLIC / Submit Answers
- Endpoint: POST /api/v1/clinical-ops/public/order/{token}/submit
- Auth: Public Token
- Called By: Patient Device
- Purpose: Submit assessment answers
- Success: 200 { status }
- Errors: 400, 410

## STAFF / Generate Report PDF
- Endpoint: POST /api/v1/clinical-ops/staff/reports/generate
- Auth: Staff JWT
- Called By: Staff Dashboard
- Purpose: Generate clinical report PDF
- Success: 201 { report_id }
- Errors: 400, 403

## STAFF / Download Report
- Endpoint: GET /api/v1/clinical-ops/staff/reports/download
- Auth: Staff JWT
- Called By: Staff Dashboard
- Purpose: Download generated report
- Success: 200 { pdf }
- Errors: 403, 404

## PUBLIC / Download Report
- Endpoint: GET /api/v1/clinical-ops/public/order/{token}/report.pdf
- Auth: Public Token
- Called By: Patient Device
- Purpose: Download public report PDF
- Success: 200 { pdf }
- Errors: 404, 410

## STAFF / Override Validation Status
- Endpoint: POST /api/v1/clinical-ops/staff/reports/signoff/override
- Auth: Staff JWT
- Called By: Staff Dashboard
- Purpose: Override automated validation status
- Success: 200 { status }
- Errors: 403

## PUBLIC / Get Consent
- Endpoint: GET /api/v1/clinical-ops/public/order/{token}/consent
- Auth: Public Token
- Called By: Patient Device
- Purpose: Fetch consent text
- Success: 200 { consent }
- Errors: 404, 410

## PUBLIC / Submit Consent
- Endpoint: POST /api/v1/clinical-ops/public/order/{token}/consent/submit
- Auth: Public Token
- Called By: Patient Device
- Purpose: Submit patient consent
- Success: 200 { status }
- Errors: 400, 410

## PUBLIC / Request Report Access Code
- Endpoint: POST /api/v1/clinical-ops/public/order/{token}/report/access-code
- Auth: Public Token
- Called By: Patient Device
- Purpose: Request report access code
- Success: 200 { status }
- Errors: 400, 410

## ADMIN / Approve Data Deletion
- Endpoint: POST /api/v1/clinical-ops/admin/data-deletion/approve
- Auth: Admin JWT
- Called By: Admin Console
- Purpose: Approve patient data deletion request
- Success: 200 { status }
- Errors: 403
