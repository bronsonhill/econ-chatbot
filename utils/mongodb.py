from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
from datetime import datetime
import streamlit as st

def get_mongo_client(connection_string):
    return MongoClient(connection_string, server_api=ServerApi('1'))

def check_identifier(connection_string, identifier):
    """Check if the identifier exists in the valid_identifiers collection."""
    client = get_mongo_client(connection_string)
    db = client.rabbitbot
    try:
        result = db.valid_identifiers.find_one({"identifier": identifier})
        return bool(result)
    finally:
        client.close()

def log_message(connection_string, conversation_type, message, message_index=None):
    """Append a single message to the transcript document in real-time"""
    client = get_mongo_client(connection_string)
    db = client.rabbitbot
    collection = db.transcripts

    try:
        if conversation_type == "rabbit_study":
            user_identifier = st.session_state.get("user_identifier", "anonymous")
            openai_conversation_id = st.session_state.get("openai_conversation_id")
            
            # Create a unique session key based on user identifier and OpenAI conversation ID
            # Use session_id as fallback if openai_conversation_id is not available yet
            session_id = st.session_state.get("session_id", "unknown_session")
            session_key = f"{user_identifier}_{openai_conversation_id}" if openai_conversation_id else f"{user_identifier}_{session_id}"
            
            # Prepare the message with timestamp
            message_with_timestamp = {
                "message": message,
                "timestamp": datetime.utcnow(),
                "message_index": message_index
            }
            
            # Try to find existing transcript for this session
            existing_transcript = collection.find_one({
                "session_key": session_key,
                "conversation_type": "rabbit_study"
            })
            
            if existing_transcript:
                # Append message to existing transcript
                result = collection.update_one(
                    {"session_key": session_key, "conversation_type": "rabbit_study"},
                    {
                        "$push": {"messages": message_with_timestamp},
                        "$set": {
                            "last_updated": datetime.utcnow(),
                            "message_count": existing_transcript.get("message_count", 0) + 1
                        }
                    }
                )
                return str(existing_transcript["_id"])
            else:
                # Create new transcript document
                document = {
                    "session_key": session_key,
                    "timestamp": datetime.utcnow(),
                    "last_updated": datetime.utcnow(),
                    "messages": [message_with_timestamp],
                    "identifier": user_identifier,
                    "openai_conversation_id": openai_conversation_id,
                    "conversation_type": "rabbit_study",
                    "prompt_version": st.session_state.get("current_prompt", "rabbit_v1"),
                    "message_count": 1
                }
                result = collection.insert_one(document)
                return str(result.inserted_id)
    finally:
        client.close()

def log_transcript(connection_string, conversation_type, messages):
    """Mark the conversation as completed - messages are already saved in real-time"""
    client = get_mongo_client(connection_string)
    db = client.rabbitbot
    collection = db.transcripts

    try:
        if conversation_type == "rabbit_study":
            user_identifier = st.session_state.get("user_identifier", "anonymous")
            openai_conversation_id = st.session_state.get("openai_conversation_id")
            
            # Create a unique session key based on user identifier and OpenAI conversation ID
            # Use session_id as fallback if openai_conversation_id is not available yet
            session_id = st.session_state.get("session_id", "unknown_session")
            session_key = f"{user_identifier}_{openai_conversation_id}" if openai_conversation_id else f"{user_identifier}_{session_id}"
            
            # Find the existing transcript and mark it as completed
            existing_transcript = collection.find_one({
                "session_key": session_key,
                "conversation_type": "rabbit_study"
            })
            
            if existing_transcript:
                # Mark conversation as completed
                result = collection.update_one(
                    {"session_key": session_key, "conversation_type": "rabbit_study"},
                    {
                        "$set": {
                            "conversation_completed": True,
                            "completed_at": datetime.utcnow(),
                            "last_updated": datetime.utcnow()
                        }
                    }
                )
                return str(existing_transcript["_id"])
            else:
                # Fallback: create a new document if somehow no transcript exists
                document = {
                    "session_key": session_key,
                    "timestamp": datetime.utcnow(),
                    "last_updated": datetime.utcnow(),
                    "messages": [{"message": msg, "timestamp": datetime.utcnow(), "message_index": i} for i, msg in enumerate(messages)],
                    "identifier": user_identifier,
                    "openai_conversation_id": openai_conversation_id,
                    "conversation_type": "rabbit_study",
                    "prompt_version": st.session_state.get("current_prompt", "rabbit_v1"),
                    "message_count": len(messages),
                    "conversation_completed": True,
                    "completed_at": datetime.utcnow()
                }
                result = collection.insert_one(document)
                return str(result.inserted_id)
    finally:
        client.close()

def update_session_key(connection_string, old_session_key, new_session_key, conversation_type="rabbit_study"):
    """Update session key when OpenAI conversation ID becomes available"""
    client = get_mongo_client(connection_string)
    db = client.rabbitbot
    collection = db.transcripts

    try:
        # Find transcript with old session key
        old_transcript = collection.find_one({
            "session_key": old_session_key,
            "conversation_type": conversation_type
        })
        
        if old_transcript:
            # Check if transcript with new session key already exists
            new_transcript = collection.find_one({
                "session_key": new_session_key,
                "conversation_type": conversation_type
            })
            
            if new_transcript:
                # Merge messages from old transcript to new transcript
                result = collection.update_one(
                    {"session_key": new_session_key, "conversation_type": conversation_type},
                    {
                        "$push": {"messages": {"$each": old_transcript.get("messages", [])}},
                        "$set": {
                            "last_updated": datetime.utcnow(),
                            "message_count": new_transcript.get("message_count", 0) + len(old_transcript.get("messages", []))
                        }
                    }
                )
                # Delete old transcript
                collection.delete_one({"_id": old_transcript["_id"]})
                return str(new_transcript["_id"])
            else:
                # Update session key in existing transcript
                result = collection.update_one(
                    {"_id": old_transcript["_id"]},
                    {"$set": {"session_key": new_session_key}}
                )
                return str(old_transcript["_id"])
        
        return None
    finally:
        client.close()