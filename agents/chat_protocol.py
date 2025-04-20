from datetime import datetime
from uuid import uuid4

from uagents import Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec
)

def create_text_chat(text: str, end_session: bool = True) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(
        timestamp=datetime.now(),
        msg_id=uuid4(),
        content=content,
    )

chat_proto = Protocol(spec=chat_protocol_spec)

@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    try:
        # Always send acknowledgment first
        await ctx.send(
            sender,
            ChatAcknowledgement(timestamp=datetime.now(datetime.UTC), acknowledged_msg_id=msg.msg_id),
        )

        for item in msg.content:
            if isinstance(item, StartSessionContent):
                ctx.logger.info(f"Got a start session message from {sender}")
                continue
            elif isinstance(item, TextContent):
                ctx.logger.info(f"Got a message from {sender}: {item.text}")
                # Store sender and query for agent to handle
                ctx.storage.set("current_sender", sender)
                ctx.storage.set("current_query", item.text)
                ctx.storage.set("current_msg_id", str(msg.msg_id))
            else:
                # If we get an error, send it back as a chat message
                await ctx.send(
                    sender,
                    create_text_chat(f"Error: Unexpected content type", end_session=True)
                )
    except Exception as e:
        # Send errors back as chat messages instead of ErrorMessage
        await ctx.send(
            sender,
            create_text_chat(f"Error: {str(e)}", end_session=True)
        )

@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(
        f"Got an acknowledgement from {sender} for {msg.acknowledged_msg_id}"
    )
