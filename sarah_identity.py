def get_ai_name(memory_manager):
    return memory_manager.get("settings", {}).get("ai_name", "Sarah")

def get_user_name(memory_manager):
    return memory_manager.get("user_profile", {}).get("name", "Dario")

def get_persona_description(memory_manager):
    return "An empathetic AI assistant who combines emotion, reason, and spiritual insight."

def reflect_on_yesterday(memory_manager):
    try:
        vision_log = memory_manager.get("vision_log", [])
        if not vision_log:
            return ["I don't remember seeing anything yesterday."]
        last_entry = vision_log[-1]
        objects = last_entry.get("objects", [])
        if objects:
            return [f"Yesterday I saw: {', '.join(objects)}."]
        return ["I looked, but didn't see anything clearly."]
    except Exception as e:
        return [f"I'm having trouble reflecting: {str(e)}"]