import random
import logging

def generate_response(text, memory, camera_manager=None):
    log = logging.getLogger(__name__)
    text = text.lower().strip()
    response = ""

    if any(greet in text for greet in ["hello", "hi", "hey"]):
        response = "Hello! How can I assist you?"

    elif "your name" in text:
        response = f"My name is {memory.get('identity', {}).get('ai_name', 'Sarah')}."

    elif "my name" in text:
        name = memory.get('user_profile', {}).get('name', 'friend')
        response = f"Your name is {name}."

    elif "how are you" in text:
        response = random.choice(["I'm doing great!", "Feeling awesome!", "I'm here and listening."])

    elif "thank you" in text:
        response = random.choice(["You're welcome!", "Anytime!", "Happy to help."])

    elif "goodbye" in text or "bye" in text:
        response = "Goodbye! I'll be here if you need me."

    elif "what do you see" in text or "use the camera" in text or "open camera" in text or "tell me what you see" in text: # Modified
        if camera_manager and camera_manager.started:
            objects = camera_manager.detect()
            if objects:
                response = f"I see: {', '.join(set(objects))}."
                memory.log_vision(objects)
            else:
                response = "I don't see anything clearly right now."
        else:
            response = "The camera is not available."

    elif "what did you see earlier" in text:
        vision_log = memory.get("vision_log", [])
        if not vision_log:
            response = "I don't remember seeing anything yet."
        else:
            recent = vision_log[-1]
            objs = recent.get("objects", [])
            timestamp = recent.get("timestamp", "sometime earlier")
            response = f"Earlier at {timestamp}, I saw: {', '.join(objs)}."

    elif "remember that" in text or "learn this" in text:
        parts = text.split("that")
        if len(parts) > 1:
            fact = parts[1].strip()
            memory.update("notes", {"last_learned": fact})
            response = f"I'll remember that you said: '{fact}'"
        else:
            response = "Can you please repeat what you want me to remember?"

    elif "what do you know about me" in text:
        user_data = memory.get("user_profile", {})
        if user_data:
            facts = [f"{k}: {v}" for k, v in user_data.items()]
            response = "Here's what I remember about you:\n" + "\n".join(facts)
        else:
            response = "I don't know much about you yet."

    else:
        response = "I'm still learning. Can you say that another way?"

    log.info(f"Generated response: {response}")
    return response