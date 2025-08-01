from openai import OpenAI
import json
import time

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="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",
)

def try_horizon_alpha_alternative_configs():
    """Try horizon-alpha with different configurations"""
    print("=== Trying horizon-alpha with alternative configurations ===\n")
    
    # Test 1: Minimal headers
    print("1. Testing with minimal headers...")
    try:
        completion = client.chat.completions.create(
          model="openrouter/horizon-alpha",
          messages=[
            {
              "role": "user",
              "content": "Hello"
            }
          ]
        )
        
        if hasattr(completion, 'error') and completion.error:
            print(f"❌ Error: {completion.error}")
        elif completion and hasattr(completion, 'choices') and completion.choices:
            print(f"✅ SUCCESS: {completion.choices[0].message.content}")
        else:
            print("❌ No response")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "-"*50 + "\n")
    
    # Test 2: Different headers
    print("2. Testing with different headers...")
    try:
        completion = client.chat.completions.create(
          extra_headers={
            "HTTP-Referer": "https://openrouter.ai",
            "X-Title": "OpenRouter Test",
          },
          model="openrouter/horizon-alpha",
          messages=[
            {
              "role": "user",
              "content": "Hello"
            }
          ]
        )
        
        if hasattr(completion, 'error') and completion.error:
            print(f"❌ Error: {completion.error}")
        elif completion and hasattr(completion, 'choices') and completion.choices:
            print(f"✅ SUCCESS: {completion.choices[0].message.content}")
        else:
            print("❌ No response")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "-"*50 + "\n")
    
    # Test 3: With temperature and max_tokens
    print("3. Testing with temperature and max_tokens...")
    try:
        completion = client.chat.completions.create(
          extra_headers={
            "HTTP-Referer": "https://valor-ivx.com",
            "X-Title": "Valor IVX",
          },
          model="openrouter/horizon-alpha",
          temperature=0.7,
          max_tokens=100,
          messages=[
            {
              "role": "user",
              "content": "Hello"
            }
          ]
        )
        
        if hasattr(completion, 'error') and completion.error:
            print(f"❌ Error: {completion.error}")
        elif completion and hasattr(completion, 'choices') and completion.choices:
            print(f"✅ SUCCESS: {completion.choices[0].message.content}")
        else:
            print("❌ No response")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "-"*50 + "\n")
    
    # Test 4: Check if it's a regional issue - try different approach
    print("4. Checking if this is a regional/provider issue...")
    try:
        # Try to get more info about the model
        models = client.models.list()
        horizon_alpha = None
        for model in models.data:
            if model.id == "openrouter/horizon-alpha":
                horizon_alpha = model
                break
        
        if horizon_alpha:
            print(f"✅ Model details:")
            print(f"   ID: {horizon_alpha.id}")
            print(f"   Pricing: {horizon_alpha.pricing}")
            if hasattr(horizon_alpha, 'context_length'):
                print(f"   Context Length: {horizon_alpha.context_length}")
            if hasattr(horizon_alpha, 'architecture'):
                print(f"   Architecture: {horizon_alpha.architecture}")
            
            # Check if there are any alternative models from the same provider
            print(f"\n   Looking for alternative Stealth models...")
            stealth_models = []
            for model in models.data:
                if hasattr(model, 'pricing') and model.pricing:
                    if model.pricing.get('prompt') == '0' and model.pricing.get('completion') == '0':
                        stealth_models.append(model.id)
            
            print(f"   All free models: {stealth_models[:5]}...")  # Show first 5
        else:
            print("❌ Model not found")
    except Exception as e:
        print(f"❌ Error: {e}")

def check_horizon_alpha_status():
    """Check the current status of horizon-alpha"""
    print("\n=== Horizon-Alpha Status Check ===\n")
    
    try:
        # Try a very simple request
        print("Attempting minimal request to horizon-alpha...")
        completion = client.chat.completions.create(
          model="openrouter/horizon-alpha",
          messages=[{"role": "user", "content": "Hi"}],
          max_tokens=10
        )
        
        if hasattr(completion, 'error') and completion.error:
            error = completion.error
            print(f"❌ Error Details:")
            print(f"   Message: {error.get('message', 'N/A')}")
            print(f"   Code: {error.get('code', 'N/A')}")
            print(f"   Metadata: {error.get('metadata', 'N/A')}")
            
            if error.get('code') == 502:
                print(f"\n🔍 Analysis: 502 error suggests the Stealth provider is having issues.")
                print(f"   This could be:")
                print(f"   - Temporary provider outage")
                print(f"   - Regional availability issue")
                print(f"   - Provider capacity limits")
                print(f"   - Network connectivity issues")
        else:
            print(f"✅ SUCCESS: {completion.choices[0].message.content}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    try_horizon_alpha_alternative_configs()
    check_horizon_alpha_status() 