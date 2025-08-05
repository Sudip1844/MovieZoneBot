# MovieZoneBot/utils_cleanup.py

import logging
from typing import List, Dict, Any
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class ConversationCleanup:
    """Manages automatic cleanup of conversation messages."""
    
    @staticmethod
    def track_message(context: ContextTypes.DEFAULT_TYPE, message_id: int, message_type: str = "conversation"):
        """Track a message for potential cleanup."""
        if 'tracked_messages' not in context.user_data:
            context.user_data['tracked_messages'] = []
        
        context.user_data['tracked_messages'].append({
            'message_id': message_id,
            'type': message_type
        })
    
    @staticmethod
    async def cleanup_previous_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Clean up messages from the previous conversation step."""
        from main import delete_conversation_messages
        
        tracked_messages = context.user_data.get('tracked_messages', [])
        if len(tracked_messages) > 1:  # Keep current message, delete previous ones
            messages_to_delete = [msg['message_id'] for msg in tracked_messages[:-1]]
            await delete_conversation_messages(context, update.effective_chat.id, messages_to_delete)
            
            # Keep only the current message
            context.user_data['tracked_messages'] = tracked_messages[-1:]
    
    @staticmethod
    async def cleanup_completed_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Clean up all conversation messages when conversation is complete."""
        from main import delete_conversation_messages
        
        tracked_messages = context.user_data.get('tracked_messages', [])
        if tracked_messages:
            messages_to_delete = [msg['message_id'] for msg in tracked_messages]
            await delete_conversation_messages(context, update.effective_chat.id, messages_to_delete)
            
            # Clear tracked messages
            context.user_data.pop('tracked_messages', None)

async def auto_cleanup_message(update: Update, context: ContextTypes.DEFAULT_TYPE, sent_message, preserve_for_users: bool = False):
    """
    Automatically schedule message cleanup based on user role and message type.
    
    Args:
        update: Telegram update object
        context: Bot context
        sent_message: The message that was sent by the bot
        preserve_for_users: If True, preserve this message for regular users (like movie posts)
    """
    from main import schedule_user_message_cleanup
    import database as db
    
    user_role = db.get_user_role(update.effective_user.id)
    
    # Track conversation messages for step-by-step cleanup
    if hasattr(sent_message, 'message_id'):
        ConversationCleanup.track_message(context, sent_message.message_id)
        
        # Schedule cleanup for user messages
        if update.message:
            schedule_user_message_cleanup(context, update.effective_chat.id, update.message.message_id, user_role)
        
        # For bot messages: owners/admins get everything deleted, users keep movie posts
        if not preserve_for_users or user_role in ['owner', 'admin']:
            schedule_user_message_cleanup(context, update.effective_chat.id, sent_message.message_id, user_role)

def get_cleanup_delay(user_role: str, message_type: str = "normal") -> int:
    """Get cleanup delay based on user role and message type."""
    if user_role in ['owner', 'admin']:
        return 86400  # 24 hours for all messages
    else:
        if message_type == "movie_post":
            return -1  # Never delete movie posts for users
        return 86400  # 24 hours for other messages