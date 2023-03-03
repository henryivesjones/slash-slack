from typing import List, Optional, Union


def _make_mrkdown_block(mrkdown: str):
    """
    Wraps the mrkdown in a block kit block.
    """
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": mrkdown,
        },
    }


def _make_header_block(heading: str):
    """
    Wraps the heading in a block kit block.
    """
    return {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": heading,
        },
    }


def _make_block_message(
    blocks: Union[None, str, dict, List[Union[str, dict]]],
    header: Optional[str] = None,
    visible_in_channel: bool = True,
):
    """
    Generates slack block kit messages from a variety of input types.

    str -> Wrap the str in a mrkdown section and in a top level response.

    dict -> Wrap the dict in a top level response.

    list -> Wrap the altered contents in a top level response.

        str -> Wrap the str in a mrkdown section

        dict -> add to top level response as is
    """
    output_blocks: List[dict] = []
    if blocks is None or blocks == "":
        return {}

    if isinstance(blocks, dict):
        output_blocks = [blocks]

    elif isinstance(blocks, list):
        formatted_blocks = []
        for block in blocks:
            if isinstance(block, str):
                formatted_blocks.append(_make_mrkdown_block(block))
            if isinstance(block, dict):
                formatted_blocks.append(block)
        output_blocks = formatted_blocks
    else:
        output_blocks = [_make_mrkdown_block(str(blocks))]

    if header:
        output_blocks = [_make_header_block(header)] + output_blocks
    return {
        "blocks": output_blocks,
        "response_type": "in_channel" if visible_in_channel else "ephemeral",
    }
