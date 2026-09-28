from groq import Groq
from config import GROQ_API_KEY
from route_analysis import get_route

# Setup Groq (30s timeout so a network issue fails fast instead of hanging)
client = Groq(api_key=GROQ_API_KEY, timeout=30.0)

def ask_traffic_assistant(user_question, route_data=None):
    
    if route_data:
        context = f"""You are FlowAI, a smart traffic assistant embedded in a
route-intelligence app for Ahmedabad City.

Current route data:
- Distance: {route_data['distance_km']} km
- Duration: {route_data['duration_min']} minutes
- Congestion Index: {route_data['congestion_index']} / 10
- Traffic Level: {route_data['traffic_level']}
- Advice: {route_data['advice']}

Use this data when the question is about traffic or this route. If the
question is about something else entirely, still answer it helpfully and
accurately — don't refuse or deflect just because it's off-topic. Be
concise: max 3-4 sentences unless the question genuinely needs more."""

    else:
        context = """You are FlowAI, a smart traffic assistant embedded in a
route-intelligence app for Ahmedabad city. Answer traffic-related questions
helpfully using general knowledge of Ahmedabad where relevant. If asked
something unrelated to traffic, still answer it helpfully and accurately —
don't refuse or deflect just because it's off-topic. Be concise: max 3-4
sentences unless the question genuinely needs more."""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
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
