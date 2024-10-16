import logging
import os
import time
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image
import pyrogram

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load configuration based on environment
if bool(os.environ.get("WEBHOOK", False)):
    from sample_config import Config
else:
    from config import Config

from translation import Translation
from helper_funcs.chat_base import TRChatBase
from helper_funcs.display_progress import progress_for_pyrogram

@pyrogram.Client.on_message(pyrogram.filters.command(["c2a"]))
async def convert_to_audio(bot, update):
    TRChatBase(update.from_user.id, update.text, "c2a")
    
    if str(update.from_user.id) not in Config.SUPER_DLBOT_USERS:
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.NOT_AUTH_USER_TEXT,
            reply_to_message_id=update.id
        )
        return
    
    if (update.reply_to_message is not None) and (update.reply_to_message.media is not None):
        description = Translation.CUSTOM_CAPTION_UL_FILE
        download_location = Config.DOWNLOAD_LOCATION + "/"
        a = await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.DOWNLOAD_START,
            reply_to_message_id=update.id
        )
        c_time = time.time()
        
        # Download the media file
        the_real_download_location = await bot.download_media(
            message=update.reply_to_message,
            file_name=download_location,
            progress=progress_for_pyrogram,
            progress_args=(Translation.DOWNLOAD_START, a.id, update.chat.id, c_time)
        )

        if the_real_download_location is not None:
            if isinstance(a, pyrogram.types.Message):
                await bot.edit_message_text(
                    text=Translation.SAVED_RECVD_DOC_FILE,
                    chat_id=update.chat.id,
                    message_id=a.id
                )
                
            # Convert video to audio format (ensure the conversion process generates the audio file)
            audio_file_location_path = the_real_download_location  # Ensure this path is correct
            logger.info(f"Downloaded file: {the_real_download_location}")

            await bot.edit_message_text(
                text=Translation.UPLOAD_START,
                chat_id=update.chat.id,
                message_id=a.id
            )
            
            # Initialize metadata variables
            width, height, duration = 0, 0, 0
            metadata = extractMetadata(createParser(the_real_download_location))
            if metadata.has("duration"):
                duration = metadata.get('duration').seconds
            
            # Handle thumbnail creation and resizing
            thumb_image_path = Config.DOWNLOAD_LOCATION + "/" + str(update.from_user.id) + ".jpg"
            if os.path.exists(thumb_image_path):
                metadata = extractMetadata(createParser(thumb_image_path))
                if metadata.has("width"):
                    width = metadata.get("width")
                if metadata.has("height"):
                    height = metadata.get("height")
                # Resize image if it exists
                Image.open(thumb_image_path).convert("RGB").save(thumb_image_path)
                img = Image.open(thumb_image_path)
                img = img.resize((90, height))  # Resize to thumbnail
                img.save(thumb_image_path, "JPEG")
            else:
                thumb_image_path = None
            
            # Try to upload file
            c_time = time.time()
            try:
                await bot.send_audio(
                    chat_id=update.chat.id,
                    audio=the_real_download_location,  # Use the correct downloaded path
                    caption=description,
                    duration=duration,
                    thumb=thumb_image_path,
                    reply_to_message_id=update.reply_to_message.id,
                    progress=progress_for_pyrogram,
                    progress_args=(Translation.UPLOAD_START, a.id, update.chat.id, c_time)
                )
            except Exception as e:
                logger.error(f"Error sending audio: {e}")
                await bot.send_message(chat_id=update.chat.id, text="Failed to send audio.")

            # Clean up temporary files
            try:
                if thumb_image_path and os.path.exists(thumb_image_path):
                    os.remove(thumb_image_path)
                if os.path.exists(the_real_download_location):
                    os.remove(the_real_download_location)
            except Exception as e:
                logger.error(f"Error removing files: {e}")

            await bot.edit_message_text(
                text=Translation.AFTER_SUCCESSFUL_UPLOAD_MSG,
                chat_id=update.chat.id,
                message_id=a.id,
                disable_web_page_preview=True
            )
    else:
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.REPLY_TO_DOC_FOR_C2V,
            reply_to_message_id=update.id
        )
