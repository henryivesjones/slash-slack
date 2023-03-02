from typing import List, Union


def _make_mrkdown_block(mrkdown: str):
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": mrkdown,
        },
    }


def _make_block_message(
    blocks: Union[None, str, dict, List[Union[str, dict]]],
    visible_in_channel: bool = True,
):
    if blocks is None or blocks == "":
        return {}

    if isinstance(blocks, dict):
        blocks = [blocks]

    elif isinstance(blocks, list):
        formatted_blocks = []
        for block in blocks:
            if isinstance(block, str):
                formatted_blocks.append(_make_mrkdown_block(block))
            if isinstance(block, dict):
                formatted_blocks.append(block)
        blocks = formatted_blocks
    else:
        blocks = [_make_mrkdown_block(str(blocks))]
    return {
        "blocks": blocks,
        "response_type": "in_channel" if visible_in_channel else "ephemeral",
    }
