import requests
import time
import os
import base64
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
from io import BytesIO

from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TESTING_MODE = True
APITOKEN = 'IKUufeSqWgHXrDEGToixRqhWM4BTHyoOT9GEPZQF6Hu0g19wutXCoMYE3ZnqrasqORYTJrarJ/M=' # Your API Token

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hello! Send me a photo and I will search for it✌️.')

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user    # from 87 to 90 the code explains that for  bot uploading the photo
    photo_file = await update.message.photo[-1].get_file()
    image_path = f'{user.id}.jpg'
    await photo_file.download_to_drive(image_path)
    
    await update.message.reply_text('Photo received😊')
    await update.message.reply_text('Searching images...🔍')
    error, urls_images = await search_by_face(image_path,update,context)

    if urls_images:
        for im in urls_images:  # Iterate search results
            score = im['score']  # 0 to 100 score how well the face is matching found image
            url = im['url']  # URL to webpage where the person was found
            image_base64 = im['base64']  # Thumbnail image encoded as base64 string
            
            if score>50:
                
                try:
                # Decode the base64 image and save it
                    image_data = base64.b64decode(image_base64[24:])
                    image_result_path = f'{user.id}_result.jpg'
                    with open(image_result_path, 'wb') as f:
                        f.write(image_data)
                    print(f"Image decoded and saved as {image_result_path}")

                    # Verify the image file exists and is not empty
                    if os.path.getsize(image_result_path) == 0:
                        raise ValueError("The image file is empty")

                    # Send the image along with the score and URL
                    with open(image_result_path, 'rb') as f:
                        await context.bot.send_photo(
                            chat_id=update.message.chat_id,
                            photo=f,
                            caption=f"Find more details here: {url}😎"
                        )
                    print(f"Image sent successfully: {image_result_path}")

                # Clean up the result image file
                    os.remove(image_result_path)
                    print(f"Image file {image_result_path} deleted after sending")

                except Exception as e:
                   print(f"Failed to process and send image: {str(e)}")
                
                # # Clean up the result image file
                # os.remove(image_result_path)
                
                # await update.message.reply_text(f"{score} {url} {image_base64[:32]}...")
   
    else:
        await update.message.reply_text(error)
    
    os.remove(image_path)  # Clean up the downloaded image file

async def search_by_face(image_file: str,update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if TESTING_MODE:
        print('****** TESTING MODE search, results are inaccurate, and queue wait is long, but credits are NOT deducted ******')

    site = 'https://facecheck.id'
    headers = {'accept': 'application/json', 'Authorization': APITOKEN}

    try:
        with open(image_file, 'rb') as img_file:
            files = {'images': img_file, 'id_search': None}
            response = requests.post(f'{site}/api/upload_pic', headers=headers, files=files).json()
    except requests.RequestException as e:
        return f"Request error: {str(e)}", None

    if response.get('error'):
        return f"{response['error']} ({response.get('code')})", None

    id_search = response.get('id_search')
    print(response.get('message') + ' id_search=' + id_search)

    json_data = {'id_search': id_search, 'with_progress': True, 'status_only': False, 'demo': TESTING_MODE}
    
    while True:
        try:
            response = requests.post(f'{site}/api/search', headers=headers, json=json_data).json()
        except requests.RequestException as e:
            return f"Request error: {str(e)}", None

        if response.get('error'):
            return f"{response['error']} ({response.get('code')})", None
        if response.get('output') :
            
            return None, response['output']['items']
        
        
        print(f'{response.get("message")} progress: {response.get("progress")}%')
        time.sleep(1)

def main() -> None:
    application = Application.builder().token("7088343195:AAFffUwxrqrsjFMHYOnAMzOmui7oKAaTwMg").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    application.run_polling()

if __name__ == '__main__':
    main()
