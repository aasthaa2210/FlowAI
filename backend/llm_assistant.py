from groq import Groq
from config import GROQ_API_KEY
from route_analysis import get_route

# Setup Groq (30s timeout so a network issue fails fast instead of hanging)
client = Groq(api_key=GROQ_API_KEY, timeout=30.0)

def ask_traffic_assistant(user_question, route_data=None):
    
    if route_data:
        context = f"""You are FlowAI, a smart traffic assistant for Ahmedabad city.

Current route data:
- Distance: {route_data['distance_km']} km
- Duration: {route_data['duration_min']} minutes
- Congestion Index: {route_data['congestion_index']} / 10
- Traffic Level: {route_data['traffic_level']}
- Advice: {route_data['advice']}

Answer based on this data. Be concise and helpful. Max 3 sentences."""

    else:
        context = """You are FlowAI, a smart traffic assistant for Ahmedabad city.
Answer traffic related questions helpfully and concisely. Max 3 sentences."""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": context},
            {"role": "user", "content": user_question}
        ]
    )
    
    return response.choices[0].message.content


# Test
if __name__ == "__main__":
    print("=== FlowAI Chat Assistant ===")
    print("Loading route data...")
    
    source = [72.5714, 23.0395]  # Satellite
    dest   = [72.6019, 22.9961]  # Maninagar
    route_data = get_route(source, dest)
    
    print(f"Route loaded: {route_data['distance_km']}km | {route_data['traffic_level']}")
    print("Ask me anything! (type 'quit' to exit)")
    print("")
    
    while True:
        question = input("You: ")
        if question.lower() == "quit":
            break
        answer = ask_traffic_assistant(question, route_data)
        print(f"FlowAI: {answer}")
        print("")
