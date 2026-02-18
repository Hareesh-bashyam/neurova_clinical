# Clinical Operations API Documentation (v1)

**Base URL:** `app.nily360.com/api/v1/clinical/`


---

## Table of Contents

1. [Authentication](#authentication)
2. [Common Response Format](#common-response-format)
3. [Error Codes](#error-codes)
4. [Staff Endpoints](#staff-endpoints)
5. [Public Endpoints](#public-endpoints)
6. [Admin Endpoints](#admin-endpoints)

---

## Authentication

### Staff Endpoints
- **Authentication Required:** Yes
- **Method:** Token-based authentication (JWT/Session)
- **Header:** `Authorization: Bearer <token>`
- **Permission:** User must be authenticated and belong to the organization

### Public Endpoints
- **Authentication Required:** No
- **Access:** Token-based via URL parameter
- **Rate Limiting:** Applied via `AnonRateThrottle`

### Admin Endpoints
- **Authentication Required:** Yes
- **Permission:** Admin role required

---

## Common Response Format

All endpoints follow a consistent response structure:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { /* endpoint-specific data */ }
}
```

### Success Response
- `success`: `true`
- `message`: Human-readable success message
- `data`: Response payload (varies by endpoint)

### Error Response
- `success`: `false`
- `message`: Error description
- `data`: `null` or error details

---

## Error Codes

| HTTP Status | Description |
|-------------|-------------|
| `200` | Success |
| `201` | Created successfully |
| `400` | Bad Request - Invalid input |
| `403` | Forbidden - Unauthorized access or expired link |
| `404` | Not Found - Resource doesn't exist |
| `409` | Conflict - Invalid state transition |

---

## Staff Endpoints

### 1. Create Patient

**Endpoint:** `POST /api/v1/clinical/staff/patients/create`

**Authentication:** Required

**Description:** Creates a new patient record in the system.

**Request Body:**
```json
{
  "org_id": "uuid-string",
  "full_name": "John Doe",
  "age": 35,
  "sex": "MALE",
  "phone": "1234567890",
  "email": "john.doe@example.com",
  "mrn": "MRN12345"
}
```

**Field Validations:**
- `org_id`: Required, must match authenticated user's organization
- `full_name`: Required, minimum 3 characters
- `age`: Required, integer between 0-120
- `sex`: Required, one of: `MALE`, `FEMALE`, `OTHER`
- `phone`: Required, 8-15 digits only
- `email`: Required, valid email format
- `mrn`: Optional, medical record number

**Success Response (201):**
```json
{
  "success": true,
  "message": "Patient created successfully",
  "data": {
    "patient_id": 123
  }
}
```

**Error Responses:**
- `400`: Missing or invalid fields
- `403`: Unauthorized organization access

---

### 2. Create Order

**Endpoint:** `POST /api/v1/clinical/staff/orders/create`

**Authentication:** Required

**Description:** Creates a new assessment order for a patient.

**Request Body:**
```json
{
  "org_id": "uuid-string",
  "patient_id": 123,
  "battery_code": "MENTAL_HEALTH_BASIC",
  "battery_version": "1.0",
  "encounter_type": "OPD",
  "referring_unit": "Psychiatry",
  "administration_mode": "KIOSK",
  "verified_by_staff": true
}
```

**Field Details:**
- `org_id`: Required, organization UUID
- `patient_id`: Required, existing patient ID
- `battery_code`: Required, assessment battery identifier
- `battery_version`: Optional, defaults to "1.0"
- `encounter_type`: Optional, defaults to "OPD"
- `referring_unit`: Optional
- `administration_mode`: Optional, defaults to "KIOSK"
- `verified_by_staff`: Optional, defaults to true

**Success Response (201):**
```json
{
  "success": true,
  "message": "Order created successfully",
  "data": {
    "order_id": 456,
    "public_token": "secure-token-string",
    "public_link_expires_at": "2026-02-07T15:39:07+05:30"
  }
}
```

**Error Responses:**
- `400`: Missing required fields or validation errors
- `403`: Unauthorized organization access
- `404`: Patient not found

---

### 3. Get Clinic Queue

**Endpoint:** `GET /api/v1/clinical/staff/queue`

**Authentication:** Required

**Description:** Retrieves the latest 200 assessment orders for the organization.

**Query Parameters:** None

**Success Response (200):**
```json
{
  "success": true,
  "message": "Queue fetched successfully",
  "data": {
    "results": [
      {
        "order_id": 456,
        "patient_name": "John Doe",
        "battery_code": "MENTAL_HEALTH_BASIC",
        "status": "IN_PROGRESS",
        "created_at": "2026-02-05T10:30:00Z"
      }
    ]
  }
}
```

---

### 4. Set Delivery and Mark Delivered

**Endpoint:** `POST /api/v1/clinical/staff/orders/deliver`

**Authentication:** Required

**Description:** Sets delivery mode and marks an order as delivered.

**Request Body:**
```json
{
  "order_id": 456,
  "delivery_mode": "EMAIL",
  "delivery_target": "patient@example.com"
}
```

**Field Details:**
- `order_id`: Required
- `delivery_mode`: Required (e.g., "EMAIL", "SMS", "DOWNLOAD")
- `delivery_target`: Optional, delivery destination

**Allowed Order Status:** `COMPLETED`, `AWAITING_REVIEW`

**Success Response (200):**
```json
{
  "success": true,
  "message": "Report delivered successfully",
  "data": {
    "order_id": 456,
    "status": "DELIVERED",
    "delivery_mode": "EMAIL"
  }
}
```

**Error Responses:**
- `400`: Missing required fields
- `409`: Invalid order status for delivery

---


### 5. Generate Report PDF

**Endpoint:** `POST /api/v1/clinical/staff/reports/generate`

**Authentication:** Required

**Description:** Generates PDF report for a completed assessment.

**Request Body:**
```json
{
  "org_id": "uuid-string",
  "order_id": 456
}
```

**Allowed Order Status:** `AWAITING_REVIEW`, `DELIVERED`, `COMPLETED`

**Success Response (200):**
```json
{
  "success": true,
  "message": "Report generated successfully",
  "data": {
    "report_id": 789,
    "pdf_url": "/media/reports/NEUROVAX_REPORT_ORDER_456.pdf"
  }
}
```

**Error Responses:**
- `400`: Missing fields or invalid order status
- `403`: Unauthorized organization access

---


### 6. Clinical Inbox

**Endpoint:** `GET /api/v1/clinical/staff/inbox`

**Authentication:** Required

**Description:** Retrieves completed assessments awaiting clinical review (max 200).

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "order_id": 456,
        "patient_name": "John Doe",
        "age": 35,
        "sex": "MALE",
        "battery_code": "MENTAL_HEALTH_BASIC",
        "created_at": "2026-02-05T10:30:00Z",
        "status": "COMPLETED",
        "primary_severity": "MODERATE",
        "has_red_flags": true
      }
    ]
  }
}
```

**Filters Applied:**
- Status: `COMPLETED` only
- Deletion status: `ACTIVE`
- Organization: Current user's org

---

### 7. Clinical Review Detail

**Endpoint:** `GET /api/v1/clinical/staff/order/{order_id}/review`

**Authentication:** Required

**Description:** Retrieves detailed assessment review information for clinical staff.

**URL Parameters:**
- `order_id`: Required

**Success Response (200):**
```json
{
  "success": true,
  "message": "Assessment Review Details",
  "data": {
    "header": {
      "org_name": "Example Hospital"
    },
    "patient_summary": {
      "name": "John Doe",
      "age": 35,
      "sex": "MALE",
      "hospital_id": "MRN12345",
      "assessment_date": "February 05, 2026"
    },
    "battery_summary": {
      "items": [
        {
          "label": "Mood Assessment",
          "test_code": "PHQ9",
          "status": "COMPLETED"
        },
        {
          "label": "Anxiety Screening",
          "test_code": "GAD7",
          "status": "NOT_ATTEMPTED"
        }
      ]
    },
    "clinical_flag": {
      "visible": true,
      "type": "WARNING",
      "title": "Clinical Flag",
      "message": "Responses indicate elevated distress markers requiring clinical attention."
    },
    "audit_timeline": [
      {
        "label": "Assessment Started",
        "time": "10:30 AM"
      },
      {
        "label": "Assessment Completed",
        "time": "11:15 AM"
      },
      {
        "label": "Report Generated",
        "time": "11:20 AM"
      }
    ]
  }
}
```

**Battery Test Codes:**
- `PHQ9`: Mood Assessment
- `GAD7`: Anxiety Screening
- `STOP_BANG`: Sleep Quality
- `PSS10`: Stress Evaluation
- `AUDIT`: Alcohol Use
- `MDQ`: Mood Disorder Screening

---

## Public Endpoints

### 8. Public Order Bootstrap

**Endpoint:** `GET /api/v1/clinical/public/order/{token}`

**Authentication:** None (public access via token)

**Description:** Initializes a public assessment session using the order token.

**URL Parameters:**
- `token`: Public order token (from order creation)

**Success Response (200):**
```json
{
  "success": true,
  "message": "Order initialized successfully",
  "data": {
    "org_id": 1,
    "order_id": 456,
    "patient_id": 123,
    "patient_name": "John Doe",
    "patient_age": 35,
    "patient_gender": "MALE",
    "battery_code": "MENTAL_HEALTH_BASIC",
    "battery_version": "1.0",
    "status": "IN_PROGRESS"
  }
}
```

**Error Responses:**
- `403`: Link expired
- `404`: Invalid token

**Side Effects:**
- Marks order as started if status is `IN_PROGRESS`

---

### 9. Public Order Submit

**Endpoint:** `POST /api/v1/clinical/public/order/{token}/submit`

**Authentication:** None (public access via token)

**Description:** Submits assessment answers and completes the order.

**URL Parameters:**
- `token`: Public order token

**Request Body:**
```json
{
  "answers": [
    {
      "question_id": "PHQ9_Q1",
      "answer": 2
    },
    {
      "question_id": "PHQ9_Q2",
      "answer": 1
    }
  ],
  "duration_seconds": 450
}
```

**Field Details:**
- `answers`: Required, array of answer objects
- `duration_seconds`: Optional, defaults to 0

**Success Response (200):**
```json
{
  "success": true,
  "message": "Assessment submitted successfully",
  "data": {
    "order_id": 456
  }
}
```

**Error Responses:**
- `400`: Missing or invalid answers
- `403`: Link expired
- `409`: Order not in progress (already submitted)

**Processing:**
1. Saves raw answers
2. Computes response quality metrics
3. Scores the battery
4. Marks order as completed

**Deduplication:** Duplicate submissions are ignored (idempotent)

---

### 10. Get Consent Text

**Endpoint:** `GET /api/v1/clinical/public/order/{token}/consent`

**Authentication:** None

**Description:** Retrieves consent form text for the patient.

**URL Parameters:**
- `token`: Public order token

**Success Response (200):**
```json
{
  "success": true,
  "message": "Consent text retrieved successfully",
  "data": {
    "consent_version": "V1",
    "consent_language": "en",
    "consent_text": "Full consent text here..."
  }
}
```

---

### 11. Submit Consent

**Endpoint:** `POST /api/v1/clinical/public/order/{token}/consent/submit`

**Authentication:** None

**Description:** Records patient consent for assessment.

**URL Parameters:**
- `token`: Public order token

**Request Body:**
```json
{
  "consent_version": "V1",
  "consent_language": "en",
  "consent_given_by": "SELF",
  "guardian_name": null,
  "allow_patient_copy": true
}
```

**Field Details:**
- `consent_version`: Optional, defaults to "V1"
- `consent_language`: Optional, defaults to "en"
- `consent_given_by`: Optional, defaults to "SELF" (or "GUARDIAN")
- `guardian_name`: Required if `consent_given_by` is "GUARDIAN"
- `allow_patient_copy`: Optional, boolean

**Success Response (200):**
```json
{
  "success": true,
  "message": "Consent captured successfully",
  "data": {
    "consent_version": "V1",
    "consent_language": "en",
    "consent_given_by": "SELF",
    "allow_patient_copy": true,
    "consent_id": 789
  }
}
```

**Side Effects:**
- If `allow_patient_copy` is true, sets order delivery mode to `ALLOW_PATIENT_DOWNLOAD`
- Creates `CONSENT_CAPTURED` audit event

---

### 12. Download Report (Public)

**Endpoint:** `GET /api/v1/clinical/public/order/{token}/report.pdf`

**Authentication:** None (requires access code)

**Description:** Downloads PDF report for patients.

**URL Parameters:**
- `token`: Public order token

**Query Parameters:**
- `code`: Required, access code from request endpoint

**Success Response (200):**
- Returns PDF file
- Content-Type: `application/pdf`
- Filename: `assessment_report_{order_id}.pdf`

**Error Responses:**
- `403`: Invalid/missing access code, link expired, or download not allowed
- `404`: PDF not generated
- `409`: PDF integrity check failed

**Security Checks:**
1. Link expiry validation
2. Delivery mode must be `ALLOW_PATIENT_DOWNLOAD`
3. Valid access code required
4. PDF integrity verification (SHA-256)

---


### 1. Error Handling
Always check the `success` field in responses:

```javascript
const response = await fetch('/api/v1/clinical/staff/patients/create', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(patientData)
});

const result = await response.json();

if (result.success) {
  // Handle success
  console.log(result.data);
} else {
  // Handle error
  console.error(result.message);
}
```

### 2. Token Expiry
For public endpoints, always check token expiry before allowing user actions:

```javascript
const expiryDate = new Date(orderData.public_link_expires_at);
if (new Date() > expiryDate) {
  // Show "Link expired" message
}
```

### 3. Organization Validation
Always include the correct `org_id` in staff requests to prevent authorization errors.

### 4. Rate Limiting
Public endpoints have rate limiting. Implement retry logic with exponential backoff.

### 5. File Downloads
For PDF downloads, handle as blob:

```javascript
const response = await fetch('/api/v1/clinical/staff/reports/download?order_id=456');
const blob = await response.blob();
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'report.pdf';
a.click();
```

---

## Support

For questions or issues, contact the backend development team.

**API Version:** v1  
**Last Updated:** February 2026
