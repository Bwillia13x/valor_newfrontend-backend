from openai import OpenAI
import time
import datetime

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="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",
)

def test_horizon_alpha():
    """Test if horizon-alpha is working"""
    try:
        completion = client.chat.completions.create(
          model="openrouter/horizon-alpha",
          messages=[{"role": "user", "content": "Hi"}],
          max_tokens=10
        )
        
        if hasattr(completion, 'error') and completion.error:
            return False, completion.error
        elif completion and hasattr(completion, 'choices') and completion.choices:
            return True, completion.choices[0].message.content
        else:
            return False, "No response"
            
    except Exception as e:
        return False, str(e)

def monitor_horizon_alpha(check_interval=300):  # Check every 5 minutes
    """Monitor horizon-alpha availability"""
    print(f"🔍 Starting horizon-alpha monitoring...")
    print(f"   Check interval: {check_interval} seconds")
    print(f"   Press Ctrl+C to stop\n")
    
    check_count = 0
    
    while True:
        check_count += 1
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"[{timestamp}] Check #{check_count}: Testing horizon-alpha...")
        
        is_working, result = test_horizon_alpha()
        
        if is_working:
            print(f"🎉 SUCCESS! Horizon-alpha is working!")
            print(f"   Response: {result}")
            print(f"\n✅ You can now use horizon-alpha!")
            break
        else:
            print(f"❌ Still not working: {result}")
            print(f"   Next check in {check_interval} seconds...\n")
            
            if check_count % 12 == 0:  # Every hour
                print(f"⏰ Hourly update: Still monitoring... ({check_count} checks completed)\n")
        
        time.sleep(check_interval)

def quick_status_check():
    """Quick status check of horizon-alpha"""
    print("🔍 Quick horizon-alpha status check...")
    
    is_working, result = test_horizon_alpha()
    
    if is_working:
        print(f"✅ SUCCESS! Horizon-alpha is working!")
        print(f"   Response: {result}")
        return True
    else:
        print(f"❌ Not working: {result}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        try:
            monitor_horizon_alpha()
        except KeyboardInterrupt:
            print(f"\n🛑 Monitoring stopped by user")
    else:
        quick_status_check()
        print(f"\n💡 To start continuous monitoring, run:")
        print(f"   python3 horizon_alpha_monitor.py monitor") 