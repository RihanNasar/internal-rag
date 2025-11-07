"""Direct Brevo API test to diagnose email issues"""
import httpx
import asyncio
import os

async def test_brevo():
    # Get API key from environment
    api_key = os.getenv("BREVO_API_KEY")
    
    if not api_key:
        print("❌ BREVO_API_KEY environment variable not set!")
        print("Please set it first: $env:BREVO_API_KEY='your-api-key'")
        return
    
    print(f"🔑 Using API Key: {api_key[:20]}...")
    print(f"📧 Testing email delivery...\n")
    
    # Test 1: Check account info
    print("=" * 50)
    print("TEST 1: Checking Brevo Account Info")
    print("=" * 50)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.brevo.com/v3/account",
                headers={"api-key": api_key}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Account verified!")
                print(f"📊 Email plan: {data.get('plan', [{}])[0].get('type', 'N/A')}")
                print(f"📈 Credits remaining: {data.get('plan', [{}])[0].get('credits', 'N/A')}")
                print(f"📧 Verified senders: {len(data.get('senders', []))}")
                
                # Show sender emails
                for sender in data.get('senders', []):
                    print(f"   - {sender.get('name')} <{sender.get('email')}>")
            else:
                print(f"❌ Account check failed: {response.status_code}")
                print(f"Response: {response.text}")
                return
                
    except Exception as e:
        print(f"❌ Error checking account: {e}")
        return
    
    # Test 2: Send test email
    print("\n" + "=" * 50)
    print("TEST 2: Sending Test Email")
    print("=" * 50)
    
    test_email = "mrnzero321@gmail.com"  # Your email
    
    payload = {
        "sender": {
            "name": "Task Assignment AI",
            "email": "mrihannasar@gmail.com"
        },
        "to": [
            {
                "email": test_email,
                "name": "Test User"
            }
        ],
        "subject": "🧪 Brevo Test Email - Internal RAG System",
        "htmlContent": """
<html>
<body style="font-family: Arial; padding: 20px;">
    <h2 style="color: #667eea;">✅ Brevo Email Test Successful!</h2>
    <p>If you're reading this, your Brevo email integration is working correctly.</p>
    <p><strong>Timestamp:</strong> Test sent from diagnostic script</p>
    <div style="background: #f0f0f0; padding: 15px; margin-top: 20px; border-radius: 5px;">
        <p><strong>📊 Test Details:</strong></p>
        <ul>
            <li>Sender: Task Assignment AI</li>
            <li>Service: Brevo HTTP API</li>
            <li>Status: Direct API call (no framework)</li>
        </ul>
    </div>
</body>
</html>
        """,
        "textContent": "Brevo Test Email - If you're reading this, your email integration is working!"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.brevo.com/v3/smtp/email",
                json=payload,
                headers={
                    "api-key": api_key,
                    "content-type": "application/json"
                },
                timeout=30.0
            )
            
            if response.status_code == 201:
                result = response.json()
                print(f"✅ Email sent successfully!")
                print(f"📧 To: {test_email}")
                print(f"🆔 Message ID: {result.get('messageId', 'N/A')}")
                print(f"\n⏳ Check your inbox (and spam folder) at {test_email}")
            else:
                print(f"❌ Email send failed: {response.status_code}")
                print(f"Response: {response.text}")
                
                # Parse error details
                try:
                    error_data = response.json()
                    print(f"\n🔍 Error details:")
                    print(f"   Code: {error_data.get('code', 'N/A')}")
                    print(f"   Message: {error_data.get('message', 'N/A')}")
                except:
                    pass
                    
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_brevo())
