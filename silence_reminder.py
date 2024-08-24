from nonebot import require, on_message, get_driver, get_bot
from nonebot.adapters.onebot.v11 import Bot, Message, Event, GroupMessageEvent
from nonebot.rule import Namespace, ArgumentParser

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

import time

from src.plugins.shengjing.models import *


reminder = on_message()


last_message_time = {}  # Grouped by group_id
is_last_message_from_bot = False


@reminder.handle()
async def default(bot: Bot, event: GroupMessageEvent):
    global last_message_time, is_last_message_from_bot

    last_message_time[event.group_id] = time.time()
    is_last_message_from_bot = False
    # await reminder.send(str(last_message_time))  #  DEBUG


@scheduler.scheduled_job("interval", seconds=10)
async def check_silence():
    global last_message_time, is_last_message_from_bot
    now = time.time()
    bot = get_bot()

    for group_id, last_time in last_message_time.items():
        if (
            now - last_time > 10 * 60 and is_last_message_from_bot is False
        ):  # 10 minutes
            await bot.send_group_msg(
                group_id=group_id,
                message=MessageSegment.text("好安静啊，来条圣经看看吧！"),
            )
            await bot.send_group_msg(
                group_id=group_id, message=await get_random_quotation()
            )
            last_message_time[group_id] = now
            is_last_message_from_bot = True
