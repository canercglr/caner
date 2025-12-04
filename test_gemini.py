#!/usr/bin/env python3
"""
Quick test script for Gemini API
"""
import requests
import json
import sys

def test_gemini(api_key: str, topic: str = "Yapay Zeka"):
    """Test Gemini API with a simple request."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    prompt = f"""Sen bir eğitim içeriği uzmanısın. "{topic}" konusu hakkında kısa bir açıklama yaz.

    JSON formatında yanıt ver:
    {{
        "topic": "{topic}",
        "summary": "Kısa açıklama",
        "key_points": ["Nokta 1", "Nokta 2", "Nokta 3"]
    }}

    Sadece JSON döndür, başka bir şey yazma."""

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    headers = {"Content-Type": "application/json"}

    print(f"🔄 Gemini API test ediliyor...")
    print(f"📝 Konu: {topic}")
    print("-" * 40)

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]

            # Clean up markdown if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]

            print("✅ API çalışıyor!")
            print("-" * 40)
            print("Yanıt:")
            print(text.strip())
            return True
        else:
            print(f"❌ Hata: {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python test_gemini.py YOUR_API_KEY [konu]")
        print("Örnek: python test_gemini.py AIzaSy... 'Güneş Sistemi'")
        sys.exit(1)

    api_key = sys.argv[1]
    topic = sys.argv[2] if len(sys.argv) > 2 else "Yapay Zeka"

    test_gemini(api_key, topic)
