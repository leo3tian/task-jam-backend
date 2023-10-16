from fastapi import FastAPI
from models import Todo
import time

# Openai API
import openai

# Make a .txt file called openai_key and put your key there
# API keys can be found and created at https://platform.openai.com/account/api-keys
openai.api_key = open("openai_key.txt", "r").readline()

# FIREBASE:
import firebase_admin
from firebase_admin import credentials
# This is what we're gonna use to communicate with firestore database
from firebase_admin import firestore

# Creating a certificate containing our credentials
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# Stores the client to our firestore database and what we'll use to talk to our database.
db = firestore.client()

# Every time a match is made, every single task involved in the match is processed by ChatGPT
# to detect if the task is malicious or harmful. If so, a placeholder is put in place of the
# malicious task.
def check(docID):
    docTodos = db.collection("todos").document(docID).get().to_dict()["todos"]
    print(docTodos)
    i = 0
    for element in docTodos:
        gptOutput = summarize(element)
        if(gptOutput == "UNSAFE"):
            list = db.collection("todos").document(docID).get().to_dict()
            list["todos"][i]["text"] = "Planting a beautiful garden🌱"
            db.collection("todos").document(docID).set(list)
        i += 1

# Asking chatGPT to review a task name, stored in the variable "self"
def summarize(self):
        messages = [{"role": "system", "content": "You will be given a task that a user created in a to-do program. Return the exact string \"UNSAFE\" if the task is malicious, dangerous, or offensive. Otherwise, return \"SAFE\""}, 
                    {"role": "user", "content": str(self)}]
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, temperature=0)
        return response.choices[0].message["content"]

# Matchmaking while loop - if you want to shut it down just delete the terminal that it's running in lol
# TODO: Gotta fix all the variable names in this lmao
word = ""
while(word != "q"):
    # Getting all users in lobby, ordered by timestamp (earlist = first)
    lobbyUsers = db.collection("lobby").order_by("timeJoined").get()
    print(lobbyUsers)
    if(len(lobbyUsers) >= 2):
        
        # storing first and second users in the lobby
        firstUser = db.collection("lobby").document(lobbyUsers[0].to_dict()["uid"]).get()
        secondUser = db.collection("lobby").document(lobbyUsers[1].to_dict()["uid"]).get()
        # print for debug
        print(firstUser.to_dict())
        print(secondUser.to_dict())
        # creating document in matches for first and second user, setting their match field to the other user
        db.collection("matches").document(firstUser.to_dict()["uid"]).set({'uid':firstUser.to_dict()["uid"], 'match':secondUser.to_dict()["uid"]})
        db.collection("matches").document(secondUser.to_dict()["uid"]).set({'uid':secondUser.to_dict()["uid"], 'match':firstUser.to_dict()["uid"]})
        print("Matched " + firstUser.to_dict()["uid"] + " with " + secondUser.to_dict()["uid"])

        # Checking every single task of both users 
        check(lobbyUsers[0].to_dict()["uid"])
        check(lobbyUsers[1].to_dict()["uid"])

        # deleting both users from lobby
        db.collection("lobby").document(lobbyUsers[0].to_dict()["uid"]).delete()
        db.collection("lobby").document(lobbyUsers[1].to_dict()["uid"]).delete()
    else:
        print("not enough users found")
    time.sleep(1)
