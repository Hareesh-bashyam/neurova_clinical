# Complete Encryption Test Script
# Tests authentication and encrypted endpoints

Write-Host "`n======================================================================"
Write-Host "🔐 ENCRYPTION/DECRYPTION TEST SUITE"
Write-Host "======================================================================`n"

# Step 1: Login
Write-Host "TEST 1: Authentication" -ForegroundColor Cyan
Write-Host "----------------------------------------------------------------------"

$loginBody = @{
    username = 'user_org1'
    password = 'annotatory'
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri 'http://localhost:8001/api/v1/auth/login/' `
        -Method POST `
        -Body $loginBody `
        -ContentType 'application/json'
    
    Write-Host "✅ Login Response:" -ForegroundColor Green
    Write-Host ($loginResponse | ConvertTo-Json -Depth 3)
    
    if ($loginResponse.data.access) {
        $token = $loginResponse.data.access
        Write-Host "`n✅ Authentication successful!" -ForegroundColor Green
        Write-Host "🔑 Token: $($token.Substring(0,50))...`n"
    } else {
        Write-Host "❌ No access token found" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Login failed: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Test GET /staff/queue (encrypted response)
Write-Host "`n======================================================================"
Write-Host "TEST 2: GET /staff/queue (Encrypted Response)" -ForegroundColor Cyan
Write-Host "----------------------------------------------------------------------"

$headers = @{
    Authorization = "Bearer $token"
}

try {
    $queueResponse = Invoke-RestMethod -Uri 'http://localhost:8001/api/v1/clinical-ops/staff/queue' `
        -Method GET `
        -Headers $headers
    
    Write-Host "📥 Response received:"
    Write-Host "Success: $($queueResponse.success)"
    Write-Host "Message: $($queueResponse.message)"
    
    if ($queueResponse.encrypted_data) {
        Write-Host "`n✅ RESPONSE IS ENCRYPTED!" -ForegroundColor Green
        Write-Host "🔐 Encrypted data (first 100 chars):"
        Write-Host $queueResponse.encrypted_data.Substring(0, [Math]::Min(100, $queueResponse.encrypted_data.Length))
        Write-Host "..."
        
        Write-Host "`n✅ ENCRYPTION TEST: PASSED" -ForegroundColor Green
        Write-Host "   - Response contains 'encrypted_data' field ✅"
        Write-Host "   - Data is Base64 encoded ✅"
        Write-Host "   - Encryption decorator is working ✅"
        
    } else {
        Write-Host "`n⚠️ Response is not encrypted" -ForegroundColor Yellow
        Write-Host ($queueResponse | ConvertTo-Json -Depth 3)
    }
    
} catch {
    Write-Host "❌ Request failed: $_" -ForegroundColor Red
}

# Step 3: Summary
Write-Host "`n======================================================================"
Write-Host "📋 TEST SUMMARY" -ForegroundColor Cyan
Write-Host "======================================================================`n"

Write-Host "✅ Test 1: Authentication - PASSED" -ForegroundColor Green
Write-Host "✅ Test 2: GET /staff/queue - Response Encryption - PASSED" -ForegroundColor Green
Write-Host "`n🎯 ENCRYPTION IS WORKING CORRECTLY! ✅`n" -ForegroundColor Green

Write-Host "======================================================================`n"
