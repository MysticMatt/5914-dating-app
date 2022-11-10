import time, tweepy, config
import tkinter as tk
import DataGetter
import meaningcloud
import profile
import json, jsons, os
from elasticsearch import Elasticsearch
import matching


def main():

    ELASTIC_PASSWORD = config.elastic_pass

    client = tweepy.Client(bearer_token=config.bearer_token)
    es = Elasticsearch(hosts = 'https://localhost:9200' , basic_auth=["elastic", ELASTIC_PASSWORD], verify_certs=False)

    getdata = input("yes to add/update profiles: ")
    if getdata == "yes":
        DataGetter.TwitterDataGetter.get_data(client,es)

    window = tk.Tk()

    window.rowconfigure(0, minsize=50)
    window.columnconfigure([0, 1, 2, 3], minsize=50)

    greeting = tk.Label(text="MVP UI")

    #greeting.pack()
    greeting.grid(row=0,column=1)

    label1 = tk.Label(text="Enter Your Username:")
    e = tk.Entry()

    label2 = tk.Label(text="Enter how many matches you want:")
    output = tk.Entry()

    tweetList = tk.Listbox(width=150, height=30)

    def e_click():
        tweetList.delete(0,tk.END)

        es = Elasticsearch(hosts = 'https://localhost:9200' , basic_auth=["elastic", ELASTIC_PASSWORD], verify_certs=False)

        usr = e.get()
        numInput = output.get()

        if numInput.isnumeric():
            numberofmatches = int(numInput)
        else:
            tweetList.insert(tk.END,"Invalid number of matches inputted!")
            return
            
        if es.exists(index="profiles", id=usr):
            user = es.get(index="profiles", id=usr)
            yourProfile = jsons.load(user['_source'], profile.Profile)
            yourPositivity = yourProfile.positivity
            yourTopics = yourProfile.topics

            Profiles = {}
            resp = es.search(index="profiles", query={"match_all": {}}, size=10000)
            for person in resp['hits']['hits']:
                Profiles[person['_source']['username']] = person['_source']
            
            matchesmade = matching.simple(yourPositivity, yourTopics, Profiles, usr)
            count = 0
            tweetList.insert(tk.END,"Your Topics: " + str(list(yourTopics.keys())))
            tweetList.insert(tk.END,"Your Positivity: " + str(round(yourPositivity,3)))
            tweetList.insert(tk.END,"")
            for match in matchesmade[0]:
                if count == numberofmatches:
                    break
                tweetList.insert(tk.END,"Twitter handle: " + str(match))
                tweetList.insert(tk.END,"Your Shared Topics: " + str(matchesmade[0][match]))
                tweetList.insert(tk.END,"Shared Topic Count: " + str(len(matchesmade[0][match])))
                tweetList.insert(tk.END,"Their Positivity: " + str(round(matchesmade[1][match],3)))
                tweetList.insert(tk.END,"Proximity to your Positivity: " + str(round(matchesmade[1][match] - yourPositivity,3)))
                tweetList.insert(tk.END,"")
                count +=1
        else:
            tweetList.insert(tk.END,"Your twitter handle isn't in our database yet! Press \"Create/Update Profile\" to add yourself to it!")
    
    def u_click():
        tweetList.delete(0,tk.END)
        es = Elasticsearch(hosts = 'https://localhost:9200' , basic_auth=["elastic", ELASTIC_PASSWORD], verify_certs=False)

        usr = e.get()
        usr = usr.lower()
        if es.exists(index="profiles", id=usr):
            user = es.get(index="profiles", id=usr)
            Profile = jsons.load(user['_source'], profile.Profile)
            yourTweets = DataGetter.TwitterDataGetter.get_users_tweets(usr,25,client)
            if len(yourTweets) > 0:
                tweetList.insert(tk.END,"Updating your profile! This may take awhile...")
                window.update()
                Profile = DataGetter.TwitterDataGetter.updateProfile(Profile, yourTweets)
                tweetList.insert(tk.END,"Your profile has been updated! You may now press \"Find Matches\"!")
            else:
                tweetList.insert(tk.END,"No tweets were found! Are you sure you entered the right username?")
        else:
            yourTweets = DataGetter.TwitterDataGetter.get_users_tweets(usr,50,client)
            if len(yourTweets) > 0:
                tweetList.insert(tk.END,"Creating your profile! This may take awhile...")
                window.update()
                Profile = DataGetter.TwitterDataGetter.generateProfile(usr, yourTweets)
                tweetList.insert(tk.END,"Your profile has been created! You may now press \"Find Matches\"!")
            else:
                tweetList.insert(tk.END,"No tweets were found! Are you sure you entered the right username?")
        
        es.index(index="profiles", id=usr, document=jsons.dumps(Profile))

    enter = tk.Button(
        text="Find Matches",
        command = lambda: e_click(),
        width=25,
        height=2,
        bg="white",
        fg="black",
    )

    update = tk.Button(
        text="Create/Update Profile",
        command = lambda: u_click(),
        width=25,
        height=2,
        bg="white",
        fg="black",
    )

    label1.grid(row = 2, column = 0,padx=5,pady=5)
    e.grid(row=2,column=1,padx=5,pady=5)

    label2.grid(row = 3, column = 0,padx=5,pady=5)
    output.grid(row=3,column=1,padx=5,pady=5)

    enter.grid(row=2, column=3,padx=5,pady=5)
    update.grid(row=3, column=3,padx=5,pady=5)
    tweetList.grid(row = 4, column = 1,padx=5,pady=5)

    window.mainloop()

if __name__ == "__main__":
    main()
