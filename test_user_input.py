# test_system.py
import requests
import time

BACKEND_URL = 'http://localhost:8000/recommend'

def test_recommendation(message, user_id="test_user_001"):
    """Test the complete system"""
    
    print("\n" + "=" * 60)
    print(f"🧪 Testing System")
    print("=" * 60)
    print(f"User: {user_id}")
    print(f"Message: {message}")
    print()
    
    payload = {
        "text": message,
        "user_id": user_id
    }
    
    try:
        print("📤 Sending to backend agent...")
        start = time.time()
        
        response = requests.post(BACKEND_URL, json=payload, timeout=35)
        
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS! ({elapsed:.2f}s)")
            print()
            print("🎬 Movie Recommendations:")
            print("-" * 60)
            print(data['reply'])
            print("-" * 60)
            print(f"Session ID: {data['session_id']}")
            print()
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>35s)")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend agent")
        print("   Make sure backend_agent.py is running on port 8001")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("=" * 60)

if __name__ == "__main__":
    # Test 1: First request
    test_recommendation("Recommend me Bitcoin documentaries")
    
    # Wait a bit
    time.sleep(3)
    
    # Test 2: Follow-up (tests conversation memory)
    test_recommendation(
        "Tell me more about the first movie",
        user_id="test_user_001"  # Same user ID
    )
    
    # Wait a bit
    time.sleep(3)
    
    # Test 3: Different user (separate conversation)
    test_recommendation(
        "Show me thriller movies about crypto",
        user_id="alice"  # Different user
    )