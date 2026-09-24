from groq import Groq
from config import GROQ_API_KEY
import json

client = Groq(api_key=GROQ_API_KEY, timeout=30.0)  # fail fast instead of hanging on network issues

def get_recommendations(traffic_data):
    """
    traffic_data = list of route results from route_analysis
    """
    
    context = """You are FlowAI's AI engine for Ahmedabad traffic management.
Based on the traffic data provided, generate exactly 6 smart recommendations.

Respond ONLY in this JSON format, nothing else:
{
  "recommendations": [
    {
      "icon": "emoji here",
      "title": "short title",
      "body": "2 sentence explanation",
      "tag": "urgent/active/pending/info",
      "color": "purple/green/amber/red/blue/pink"
    }
  ]
}"""

    prompt = f"""Current Ahmedabad traffic data:
{json.dumps(traffic_data, indent=2)}

Generate 6 smart traffic recommendations for this data."""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": context},
            {"role": "user", "content": prompt}
        ]
    )
    
    raw = response.choices[0].message.content
    
    # Clean and parse JSON
    raw = raw.strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    
    result = json.loads(raw)
    return result["recommendations"]


# Test
if __name__ == "__main__":
    
    # Sample traffic data
    traffic_data = [
        {
            "route": "Satellite → Maninagar",
            "distance_km": 8.42,
            "duration_min": 10.4,
            "congestion_index": 4.1,
            "traffic_level": "MEDIUM"
        },
        {
            "route": "Bopal → CG Road",
            "distance_km": 14.2,
            "duration_min": 28.5,
            "congestion_index": 7.8,
            "traffic_level": "HIGH"
        },
        {
            "route": "Naroda → ISCON",
            "distance_km": 18.6,
            "duration_min": 42.0,
            "congestion_index": 9.1,
            "traffic_level": "VERY HIGH"
        }
    ]
    
    print("=== FlowAI AI Recommendations ===")
    print("Generating smart recommendations...\n")
    
    recs = get_recommendations(traffic_data)
    
    for i, rec in enumerate(recs, 1):
        print(f"{i}. {rec['icon']} {rec['title']}")
        print(f"   {rec['body']}")
        print(f"   [{rec['tag'].upper()}]")
        print("")
