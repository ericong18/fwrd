import json
import re
import urllib.request
import requests

from pytube import YouTube
from flask import Flask, request, url_for
from better_profanity import profanity


app = Flask(__name__)
import youtube_transcript_api
from youtube_transcript_api import YouTubeTranscriptApi
from flask_cors import CORS
import pandas as pd

import ast

from profanity_check import predict, predict_prob

cors = CORS(app,resources={r"/*": {"origins": "*"}})

# api_key = "***PUT IN YOUR API KEY HERE***"


# url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={api_key}"
def jsonToDicts(STR):

    STRI = list(STR)
    for i in range(0,len(STRI)):
        if STRI[i] == "\"":
            STRI[i] = "\'"

    STRIN = ''.join(STRI)
    STRING = ast.literal_eval(STRIN)

    return STRING
@app.route('/', methods=['GET','POST'])
def main():

    if request.method == 'POST':
        print(request.form)
        print(request.json)

        video_id = request.form.get('video_id')
        if video_id == None:
            packet = dict(request.json)
            video_id = packet['video_id']



        print(video_id)
        try:
            data = YouTubeTranscriptApi.get_transcript(video_id)
        except youtube_transcript_api._errors.TranscriptsDisabled:
            return json.dumps({"Message":"Subtitles disabled for this video"})
        df = pd.DataFrame(data)
        print(df)

        ixs = df.loc[predict(df.text) == [1]]
        s = []
        for index, row in ixs.iterrows():
            # find the number of characters in the caption.
            # divide that number by the total length of the caption (with or without spaces)
            r = row.text.replace('\n', ' ')
            length_of_caption = len(r)
            #now that we have the denominator, we need to find the numerator
            print("r", r)
            ww = r.split()
            print(ww)
            num_chars_passed = 0
            for i in range(0, len(ww)):

                w = ww[i].split()
                print(w)
                if predict([ww[i]])== [1]:
                    ratio = (len(w) * 1.0)/length_of_caption
                    t = (ww[i], row.start, row.duration)
                    # row.duration * ratio
                    s.append(t)
                num_chars_passed += len(ww[i])

        # print(ixs)
        # ixs.start = ixs.start.round()
        # ixs.duration = ixs.duration.round()
        offending_lines = [tuple(x) for x in ixs.to_numpy()]


        if ixs.empty:
            ii = False
        else:
            ii = True

        if len(s) == 0:
            ii = False



        return json.dumps({"Message": "Hello chrome extension ppl", "curse_words":ii,  "offending_lines":jsonToDicts(json.dumps(s))})


def checkBadWordsGranualar(L):

    for w in L:
        if predict([w]) == [1]:
            return True
    return False


@app.route('/links', methods=['GET','POST'])
def links():

    if request.method=='POST':
        links = request.form.get('links')
        if links == None:
            packet = dict(request.json)
            links = packet['links']
            ii = False
            statuses = []
            # print(links)
            for link in links:
                #somehow get video from link
                video_id = link[-11:]
                df = None
                try:
                    # print("hellos")
                    df = pd.DataFrame(YouTubeTranscriptApi.get_transcript(video_id))
                    ixs = df.loc[predict(df.text) == [1]]
                    if ixs.empty:
                        ii = False
                    else:
                        for index, row in ixs.iterrows():
                            if checkBadWordsGranualar(row.text.split()):
                                ii = True
                                print(row.text)
                    statuses.append({"video_id":video_id, "curse_words":ii})

                except youtube_transcript_api._errors.VideoUnavailable:
                    # print("hellop")
                    continue
                except youtube_transcript_api._errors.TranscriptsDisabled:
                    # print("hellq")
                    continue
                except youtube_transcript_api._errors.NoTranscriptAvailable:
                    # print("hellow")
                    continue
                # print(statuses)
            return json.dumps({"Message":"Hello chrome extension ppl", "links":statuses})


@app.route('/numbadwords', methods=['GET', 'POST'])
def numbadwords():

    if request.method == 'POST':
        video_id = request.form.get('video_id')
        if video_id == None:
            packet = dict(request.json)
            video_id = packet['video_id']
        try:
            data = YouTubeTranscriptApi.get_transcript(video_id)
        except youtube_transcript_api._errors.TranscriptsDisabled:
            return json.dumps({"Message":"Subtitles disabled for this video", "num_bad_words": 0})
        except youtube_transcript_api._errors.VideoUnavailable:
            return json.dumps({"Message":"Subtitles disabled for this video", "num_bad_words": 0})
        except youtube_transcript_api._errors.TranscriptsDisabled:
            return json.dumps({"Message":"Subtitles disabled for this video", "num_bad_words": 0})
        except youtube_transcript_api._errors.NoTranscriptAvailable:
            return json.dumps({"Message":"Subtitles disabled for this video", "num_bad_words": 0})
        df = pd.DataFrame(data)
        print(df)

        ixs = df.loc[predict(df.text) == [1]]
        return json.dumps({"num_bad_words":len(ixs.index)})




        return json.dumps({"Message": "Hello chrome extension ppl", "no_curse_words":no_curse_words, "offending_lines":offending_lines})

@app.route('/test', methods=['POST'])
def comments():
    comment_dict = {}
    packet = dict(request.json)
    comments = packet['comments']
    # url = "https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&key="+g_key+"&videoId="+video_id+"&maxResults=100";
    #
    # json_url = urllib.request.urlopen(url)
    # data = json.loads(json_url.read())
    #
    for i in range(0, len(comments)):
        censored_text = profanity.censor(comments[i], '*')
        comments[i] = censored_text
    print(len(comments))
    return json.dumps({"Data": comments})


if __name__ == '__main__':
    app.run(debug=True)
