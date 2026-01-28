## STAFF / Create Order 
- Endpoint: POST /api/v1/clinical-ops/staff/orders/
- Auth: Staff JWT - Called By: Staff Dashboard 
- Purpose: Create patient order + battery 
- Success: 201 { order_id, public_token } - Errors: 400, 403