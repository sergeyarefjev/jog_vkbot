import logging
from vkbottle import Bot
from decouple import config

bot = Bot(token=config("TOKEN"))
api = bot.api
bot.labeler.vbml_ignore_case = True

admins = [int(admin) for admin in config("ADMINS").split(', ')]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)