# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

import requests

def generate_groq_text(prompt):
    """
    Generate text using Groq's Llama API based on the provided prompt.
    
    Args:
        prompt (str): The text prompt to send to the API
        
    Returns:
        str: Generated text response or error message
    """
    grok_api_key = "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"
    begin = "Introduce the mentor in a few sentences based on the following information: " + prompt
    if not grok_api_key:
        return "API key not found. Please provide a valid Groq API key."
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {grok_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": begin}],
                "temperature": 0.7,
                "max_tokens": 500
            }
        )
        
        data = response.json()
        message = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        if not message:
            return "No response generated from the API."
        
        return message
    
    except Exception as e:
        return f"Error generating text: {str(e)}"

class ActionHelloWorld(Action):

    def name(self) -> Text:
        return "action_propose_mentor"
    
    def read_mentors(self):
        # Read the mentors from a JSON file
        df = pd.read_json("actions/data.json")
        return df
    
    def get_mentor(self, df, embeddings, user_embedding, counter):
        # Calculate the cosine similarity between the user and mentor embeddings
        similarities = cosine_similarity(user_embedding, embeddings)
        # Sorts the similarity indexes
        sorted_similarities = np.argsort(similarities)
        index = sorted_similarities[0]
        # Returns the nth similar mentor
        return df.iloc[index[counter * -1]]

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        counter = tracker.get_slot("new_mentor_count") or 1
        #Increment if the user has asked for a new mentor
        if tracker.latest_message["intent"].get("name") == "ask_for_new_mentor":
            counter += 1
        if tracker.latest_message["intent"].get("name") == "tell_field" or tracker.latest_message["intent"].get("name") == "tell_work":
            counter = 1
        field = tracker.get_slot("field_of_interest") or ""
        work = tracker.get_slot("work_of_interest") or ""
        if field == "":
            dispatcher.utter_message(template="utter_ask_field")
            return []
        elif work == "":
            dispatcher.utter_message(template="utter_ask_work")
            return []
        #Embedding mentors and then proposing the best match
        df = self.read_mentors()
        if counter >= len(df):
            dispatcher.utter_message(text="No more mentors available. If you want to change preferences tell me!")
            return [SlotSet("new_mentor_count", counter)]

        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = embedding_model.encode(df['expertise'])
        user_embedding = embedding_model.encode(field + " "+ work)
        #Calculating distance between user and mentors
        best_mentor = self.get_mentor(df, embeddings, user_embedding.reshape(1, -1), counter)
        dispatcher.utter_message(text=f"Your best match is {best_mentor['name']}.")
        dispatcher.utter_message(text=generate_groq_text(best_mentor['content']))
        return [SlotSet("new_mentor_count", counter)]
