from openai import OpenAI
import json

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="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",
)

def horizon_alpha_chat(prompt, max_tokens=None, temperature=0.7):
    """Send a text message to horizon-alpha (FREE)"""
    try:
        print(f"🤖 Sending to horizon-alpha: '{prompt[:50]}...'")
        
        params = {
          "extra_headers": {
            "HTTP-Referer": "https://valor-ivx.com",
            "X-Title": "Valor IVX",
          },
          "model": "openrouter/horizon-alpha",
          "messages": [
            {
              "role": "user",
              "content": prompt
            }
          ],
          "temperature": temperature
        }
        
        if max_tokens:
            params["max_tokens"] = max_tokens
        
        completion = client.chat.completions.create(**params)
        
        if hasattr(completion, 'error') and completion.error:
            return f"❌ Error: {completion.error}"
        elif completion and hasattr(completion, 'choices') and completion.choices:
            return completion.choices[0].message.content
        else:
            return "❌ No response received"
            
    except Exception as e:
        return f"❌ Exception: {e}"

def horizon_alpha_image_analysis(image_url, question="What is in this image?", max_tokens=None):
    """Analyze an image with horizon-alpha (FREE)"""
    try:
        print(f"🖼️ Analyzing image with horizon-alpha...")
        
        params = {
          "extra_headers": {
            "HTTP-Referer": "https://valor-ivx.com",
            "X-Title": "Valor IVX",
          },
          "model": "openrouter/horizon-alpha",
          "messages": [
            {
              "role": "user",
              "content": [
                {
                  "type": "text",
                  "text": question
                },
                {
                  "type": "image_url",
                  "image_url": {
                    "url": image_url
                  }
                }
              ]
            }
          ]
        }
        
        if max_tokens:
            params["max_tokens"] = max_tokens
        
        completion = client.chat.completions.create(**params)
        
        if hasattr(completion, 'error') and completion.error:
            return f"❌ Error: {completion.error}"
        elif completion and hasattr(completion, 'choices') and completion.choices:
            return completion.choices[0].message.content
        else:
            return "❌ No response received"
            
    except Exception as e:
        return f"❌ Exception: {e}"

def test_horizon_alpha_availability():
    """Test if horizon-alpha is currently available"""
    print("🔍 Testing horizon-alpha availability...")
    
    result = horizon_alpha_chat("Hello", max_tokens=10)
    
    if result.startswith("❌"):
        print(f"❌ Horizon-alpha is not available: {result}")
        return False
    else:
        print(f"✅ Horizon-alpha is working!")
        print(f"   Response: {result}")
        return True

# Example usage functions
def example_text_conversation():
    """Example of using horizon-alpha for text conversation"""
    print("=== Horizon-Alpha Text Conversation Example ===\n")
    
    # Test basic conversation
    response = horizon_alpha_chat("Tell me a short joke about AI")
    print(f"Response: {response}\n")
    
    # Test creative writing
    response = horizon_alpha_chat("Write a haiku about coding", temperature=0.9)
    print(f"Response: {response}\n")
    
    # Test analysis
    response = horizon_alpha_chat("Explain quantum computing in simple terms", max_tokens=200)
    print(f"Response: {response}\n")

def example_image_analysis():
    """Example of using horizon-alpha for image analysis"""
    print("=== Horizon-Alpha Image Analysis Example ===\n")
    
    # Test with a nature image
    image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
    
    response = horizon_alpha_image_analysis(image_url, "What do you see in this image?")
    print(f"Response: {response}\n")
    
    response = horizon_alpha_image_analysis(image_url, "Describe the colors and mood of this scene")
    print(f"Response: {response}\n")

if __name__ == "__main__":
    print("🤖 Horizon-Alpha Client")
    print("=" * 50)
    
    # First check if it's available
    if test_horizon_alpha_availability():
        print("\n✅ Horizon-alpha is working! Running examples...\n")
        
        example_text_conversation()
        example_image_analysis()
        
        print("🎉 Examples completed!")
        print("\n💡 You can now use:")
        print("   - horizon_alpha_chat() for text conversations")
        print("   - horizon_alpha_image_analysis() for image analysis")
    else:
        print("\n❌ Horizon-alpha is not currently available.")
        print("💡 Try running the monitor script:")
        print("   python3 horizon_alpha_monitor.py monitor") 