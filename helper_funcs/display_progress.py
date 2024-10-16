import logging
import math
import os
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the correct configuration based on whether webhook is used
if bool(os.environ.get("WEBHOOK", False)):
    from sample_config import Config
else:
    from config import Config

# Import translation strings
from translation import Translation

# Progress display function for Pyrogram
async def progress_for_pyrogram(client, current, total, ud_type, message_id, chat_id, start):
    now = time.time()
    diff = now - start
    
    if total.isdigit():  # Ensure total is numeric
        total = int(total)  # Convert total to an integer

        if round(diff % 10.00) == 0 or current == total:
            percentage = current * 100 / total
            speed = current / diff
            elapsed_time = round(diff) * 1000
            time_to_completion = round((total - current) / speed) * 1000
            estimated_total_time = elapsed_time + time_to_completion

            elapsed_time = TimeFormatter(milliseconds=elapsed_time)
            estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

            # Generate progress bar
            progress = "[{0}{1}] \nP: {2}%\n".format(
                ''.join(["█" for i in range(math.floor(percentage / 5))]),
                ''.join(["░" for i in range(20 - math.floor(percentage / 5))]),
                round(percentage, 2))

            # Prepare the message text
            tmp = progress + "{0} of {1}\nSpeed: {2}/s\nETA: {3}\n".format(
                humanbytes(current),
                humanbytes(total),
                humanbytes(speed),
                estimated_total_time if estimated_total_time != '' else "0 s"
            )

            # Try to update the message with progress information
            try:
                await client.edit_message_text(
                    chat_id,
                    message_id,
                    text="{}\n {}".format(
                        ud_type,
                        tmp
                    )
                )
            except Exception as e:
                logger.error(f"Error updating progress message: {e}")
    else:
        logger.error("Total value is not numeric")

# Function to convert bytes to a human-readable format
def humanbytes(size):
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: '', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

# Function to format time in a readable format
def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
        
    return tmp[:-2]
