from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot import logger, get_driver
from pathlib import Path

from src.plugins.shengjing.config import *
from src.plugins.shengjing.hook import get_db_conn, get_db_cursor

import sqlite3
import subprocess
import os
import random


async def insert_img_quotation(image_id: int):
    conn = await get_db_conn()
    cursor = await get_db_cursor()
    sql_cmd = "INSERT INTO quotations (id, quotation, is_img) VALUES (?, '', 1)"
    await cursor.execute(sql_cmd, (image_id,))
    await conn.commit()

    logger.success(f"Tried adding image quotation, whose id is {image_id}")


async def get_max_id() -> int:
    cursor = await get_db_cursor()
    sql_cmd = "SELECT MAX(id) FROM quotations"
    await cursor.execute(sql_cmd)
    max_id_row = await cursor.fetchone()

    # Return 0 when there is no item in db
    max_id = max_id_row[0] if max_id_row[0] is not None else 0

    return max_id


def extract_image_urls(message: MessageSegment) -> list:
    image_urls = [seg.data["url"] for seg in message if seg.type == "image"]

    return image_urls


async def download_image(url: str):
    filename = os.path.join(IMG_DIR_PATH, f"{await get_max_id() + 1}.png")
    # subprocess.run(f"curl -o {filename} \"{url}\"")
    command = ["curl", "-o", filename, url]
    subprocess.run(command, capture_output=True, text=True)


async def get_img_path_by_id(id: str) -> str:
    file_path = f"{IMG_DIR_PATH}{id}.png"
    file_url = Path(file_path).as_uri()

    return file_url


async def get_quote_by_id(id: str) -> MessageSegment:
    cursor = await get_db_cursor()
    await cursor.execute("SELECT quotation, is_img FROM quotations WHERE id = ?", (id,))
    result = await cursor.fetchone()

    # ID is illegal
    if result is None:
        return MessageSegment.text("ERROR: No such ID in database or ID is illegal")

    if result[1] == 1:  # is image
        return MessageSegment.image(await get_img_path_by_id(id))
    else:  # is text
        return MessageSegment.text(result[0])


async def get_weighted_random_quote() -> MessageSegment:
    cursor = await get_db_cursor()

    # Get item count from database
    sql_cmd = "SELECT COUNT(*) FROM quotations"
    await cursor.execute(sql_cmd)
    item_count = (await cursor.fetchone())[0]

    # Get weighted random int
    # Rule: weights of resent 100 quotes are 0.6, while others are 0.4
    elements = [i for i in range(1, item_count + 1)]
    weights = [0.4] * (item_count - 100) + [0.6] * 100
    weighted_random_index = random.choices(elements, weights)[0]

    # Get quote id
    sql_cmd = "SELECT id FROM quotations ORDER BY id LIMIT 1 OFFSET ?"
    await cursor.execute(sql_cmd, (weighted_random_index - 1,))
    quote_id = (await cursor.fetchone())[0]

    # Get details of the quote
    sql_cmd = "SELECT quotation, is_img FROM quotations WHERE id = ?"
    await cursor.execute(sql_cmd, (quote_id,))
    result = await cursor.fetchone()

    quote, is_img = result

    if is_img == 1:
        # If `is_img` is 1, return a Message containing image
        file_url = await get_img_path_by_id(quote_id)
        return MessageSegment.image(file_url) + MessageSegment.text(
            f"ID: {quote_id}, Position: {weighted_random_index}, Weight: {0.6 if item_count - weighted_random_index <= 100 else 0.4}"
        )
    else:
        return MessageSegment.text(f"{quote}\n\n ID: {quote_id}")


async def get_call_count(call_type: str):
    """Get call times with a specific call type.

    Args:
        call_type (str): Possible values include:
            - "all": Sum following types up.
            - "get_random"
            - "get_by_id"
            - "add_image"
            - "get_max_id"
    """
    possible_value_list = [
        "all",
        "get_random",
        "get_by_id",
        "add_image",
        "get_max_id",
    ]
    if call_type not in possible_value_list:
        raise ValueError(
            f"Invalid call_type '{call_type}'. Must be one of {possible_value_list}"
        )

    cursor = await get_db_cursor()

    # Count all
    if call_type == "all":
        await cursor.execute("SELECT SUM(count) FROM call_counts")
        result = (await cursor.fetchone())[0]
    else:  # Select call count of the specific call_type
        await cursor.execute(
            "SELECT count FROM call_counts WHERE call_type = ?", (call_type,)
        )
        try:
            result = (await cursor.fetchone())[0]
        except TypeError:  # If call_type is not in database
            result = None

    return result


async def record_call_count(call_type: str):
    """Record call times with a specific call type.

    Args:
        call_type (str): Possible values include:
            - "get_random"
            - "get_by_id"
            - "add_image"
            - "get_max_id"

    Raises:
        ValueError: If call_type is not one of the possible values.
    """
    possible_value_list = [
        "get_random",
        "get_by_id",
        "add_image",
        "get_max_id",
    ]
    if call_type not in possible_value_list:
        raise ValueError(
            f"Invalid call_type '{call_type}'. Must be one of {possible_value_list}"
        )

    current_count = await get_call_count(call_type)

    conn = await get_db_conn()
    cursor = await get_db_cursor()

    if current_count:
        new_count = current_count + 1
        await cursor.execute(
            "UPDATE call_counts SET count = ? WHERE call_type = ?",
            (new_count, call_type),
        )
    else:
        await cursor.execute(
            "INSERT INTO call_counts (call_type, count) VALUES (?, ?)", (call_type, 1)
        )

    await conn.commit()


if __name__ == "__main__":
    pass