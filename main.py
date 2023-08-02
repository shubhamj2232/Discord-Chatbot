import chatterbot
import discord
import shutil
import config
import requests
import json
import random

from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer

from tensorflow.keras.applications.resnet50 import ResNet50
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.resnet50 import preprocess_input, decode_predictions
import numpy as np

client = discord.Client()


def get_quote():
    response = requests.get("https://zenquotes.io/api/random")
    json_data = json.loads(response.text)
    quote = json_data[0]['q'] + " -" + json_data[0]['a']
    return(quote)


def get_cases():
    response = requests.get(config.COVID_API)
    json_data = json.loads(response.text)
    x = 0
    while json_data[x]['country'] != 'India':
        x = x + 1
    stats = [json_data[x]['infected'], json_data[x]
             ['recovered'], json_data[x]['deceased']]
    return stats


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    msg = message.content.lower()
    if message.author == client.user:
        return

    if message.attachments:
        # For scanning images
        if message.attachments[0].url.endswith('jpg') or message.attachments[0].url.endswith('png') or message.attachments[0].url.endswith('jpeg'):
            await message.channel.send('I will try to recognize the object in the image')
            try:
                url = message.attachments[0].url
            except IndexError:
                print('Error: NO attachments')
                await message.channel.send('No attachments detected')
            else:
                if url[0:26] == "https://cdn.discordapp.com":
                    r = requests.get(url, stream=True)
                    imageName = 'img' + '.jpg'
                    with open(imageName, 'wb+') as destination:
                        print('Saving file ' + imageName + '...')
                        shutil.copyfileobj(r.raw, destination)

            model = ResNet50(weights='imagenet')

            img_path = 'img.jpg'
            img = image.load_img(img_path, target_size=(224, 224))
            x = image.img_to_array(img)
            x = np.expand_dims(x, axis=0)
            x = preprocess_input(x)

            preds = model.predict(x)
            await message.channel.send('It matches with the below items from my database')
            predictions = decode_predictions(preds, top=3)[0]
            for x in predictions:
                await message.channel.send(str(x[1]) + ' with a ' + str(int(x[2]*100)) + '% match')
            return
    else:
        # Intro texts
        for x in config.INTRO_ENGLISH:
            if msg.startswith(x):
                await message.channel.send(random.choice(config.REPLY_ENGLISH))
                return

        # Inspirational texts
        if any(word in msg for word in config.INSPIRE):
            quote = get_quote()
            await message.channel.send(quote)
            return

        # Corona information
        if any(word in msg for word in config.COVID_WORDS):
            await message.channel.send('Let me enlighten you with some stats from INDIA')
            info = get_cases()
            await message.channel.send("Total cases: " + str(info[0]) + ", Recovered cases: " + str(info[1]) + ", Deceased: " + str(info[2]))
            await message.channel.send('How about that?!')
            return

        # For other inputs
        else:
            await message.channel.send('Sorry, my abilities are limited since I am a bot. Ask me something else')

client.run(config.TOKEN)
