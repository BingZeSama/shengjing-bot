from nonebot import on_shell_command
from nonebot.adapters.onebot.v11 import Message, Event
from nonebot.params import CommandArg, ShellCommandArgs
from nonebot.rule import Namespace, ArgumentParser

from src.plugins.shengjing.models import *


# Define arguments of the command
parser = ArgumentParser("sj", add_help=False)
parser.add_argument("-a", "--add", help="Quotation to be added")
parser.add_argument("-h", "--help", action="store_true", help="Show help")
parser.add_argument("--max-id", action="store_true")
parser.add_argument("-i", "--img", action="store_true")
parser.add_argument("-n", "--id")
parser.add_argument("-c", "--call-count", action="store_true")

shengjing = on_shell_command(
    "圣经", aliases={"sj"}, priority=5, block=True, parser=parser
)


@shengjing.handle()
async def handle_default(args: Message = CommandArg()):
    """Handled when a user requests a random quote.

    Args:
        args (Message, optional): Defaults to CommandArg().
    """
    if not args.extract_plain_text():  # Message is only "sj"
        await record_call_count("get_random")

        await shengjing.send(await get_random_quotation())


@shengjing.handle()
async def handle_add_text(args: Namespace = ShellCommandArgs()):
    """Handled when a user adds a text quote to the database.

    Args:
        args (Namespace, optional): Defaults to ShellCommandArgs().
    """
    if quotation := args.add:
        await record_call_count("add_text")

        insert_text_quotation(quotation, get_max_id())
        await shengjing.send("添加成功")


@shengjing.handle()
async def handle_add_img(event: Event, args: Namespace = ShellCommandArgs()):
    """Handled when a user adds a image quote to the database.

    Args:
        event (Event): To retrieve the image specified by the user
        args (Namespace, optional): Defaults to ShellCommandArgs().
    """
    if args.img:
        await record_call_count("add_image")

        reply_message = (
            event.reply.message
            if hasattr(event, "reply") and event.reply
            else event.message
        )
        logger.info(str(reply_message))
        image_urls = extract_image_urls(reply_message)
        # Only require one image
        if len(image_urls) != 1:
            await shengjing.finish("错误：需要一张图片")

        download_image(image_urls[0])
        img_id = get_max_id() + 1
        insert_img_quotation(img_id)
        await shengjing.send(f"添加成功, ID: {str(img_id)}")


@shengjing.handle()
async def handle_help(args: Namespace = ShellCommandArgs()):
    """Handled when a user requests help information.

    Args:
        args (Namespace, optional): Defaults to ShellCommandArgs().
    """
    if args.help:
        await shengjing.send(help_info)


@shengjing.handle()
async def handle_max_id(args: Namespace = ShellCommandArgs()):
    """Handled when a user requests the maximum ID in the database.

    Args:
        args (Namespace, optional): Defaults to ShellCommandArgs().
    """
    if args.max_id:
        await record_call_count("get_max_id")

        await shengjing.send(f"当前最大ID: {get_max_id()}")


@shengjing.handle()
async def handle_specify_id(args: Namespace = ShellCommandArgs()):
    """Handled when a user requests the quote specified by an ID.

    Args:
        args (Namespace, optional): Defaults to ShellCommandArgs().
    """
    if args.id:
        await record_call_count("get_by_id")

        res = await get_quotation_by_id(args.id)
        await shengjing.send(res)


@shengjing.handle()
async def handle_call_counts(args: Namespace = ShellCommandArgs()):
    #     if args.call_count:
    #         logger.info(args.call_count)
    #         if count := await get_call_count(args.call_count):
    #             await shengjing.send(str(count))
    #         else:
    #             await shengjing.send(
    #                 """错误: call_type 不合法
    # call_type (str): Possible values include:
    # - \"get_random\"
    # - \"get_by_id\"
    # - \"add_text\"
    # - \"add_image\"
    # - \"get_max_id\""""
    #             )
    if args.call_count:
        await shengjing.send(str(await get_call_count("all")))


# @shengjing.handle()
# async def handle_debug(args: Namespace = ShellCommandArgs()):
#     """Only for debugging. Send the argument list.

#     Args:
#         args (Namespace, optional): Defaults to ShellCommandArgs().
#     """
#     args_dict = vars(args)
#     logger.info(str(args_dict))
#     await shengjing.send(str(args_dict))
