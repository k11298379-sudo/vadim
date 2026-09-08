from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import User, GroupChat, UserHomeworkStatus


async def get_user_by_tg_id(session: AsyncSession, tg_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    tg_id: int,
    full_name: str,
    username: Optional[str] = None,
    role: str = "pending"
) -> User:
    user = User(
        tg_id=tg_id,
        full_name=full_name,
        username=username,
        role=role
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update_user_role(session: AsyncSession, tg_id: int, role: str) -> Optional[User]:
    user = await get_user_by_tg_id(session, tg_id)
    if user:
        user.role = role
        await session.commit()
        await session.refresh(user)
    return user


async def update_user_name_and_role(
    session: AsyncSession,
    tg_id: int,
    custom_name: Optional[str] = None,
    role: str = "student"
) -> Optional[User]:
    user = await get_user_by_tg_id(session, tg_id)
    if user:
        user.role = role
        if custom_name is not None and custom_name.strip():
            user.custom_name = custom_name.strip()
        await session.commit()
        await session.refresh(user)
    return user


async def update_user_custom_name(
    session: AsyncSession,
    tg_id: int,
    custom_name: str
) -> Optional[User]:
    user = await get_user_by_tg_id(session, tg_id)
    if user:
        user.custom_name = custom_name.strip()
        await session.commit()
        await session.refresh(user)
    return user



async def get_pending_users(session: AsyncSession) -> List[User]:
    result = await session.execute(select(User).where(User.role == "pending").order_by(User.created_at))
    return list(result.scalars().all())


async def get_active_users(session: AsyncSession) -> List[User]:
    result = await session.execute(
        select(User).where(User.role.in_(["student", "admin"])).order_by(User.full_name)
    )
    return list(result.scalars().all())


async def get_notifiable_users(session: AsyncSession) -> List[User]:
    result = await session.execute(
        select(User).where(
            User.role.in_(["student", "admin"]),
            User.notifications_enabled == True
        )
    )
    return list(result.scalars().all())


async def toggle_user_notifications(session: AsyncSession, tg_id: int) -> Optional[bool]:
    user = await get_user_by_tg_id(session, tg_id)
    if user:
        user.notifications_enabled = not user.notifications_enabled
        await session.commit()
        return user.notifications_enabled
    return None


async def get_all_users(session: AsyncSession) -> List[User]:
    """Возвращает всех пользователей бота"""
    result = await session.execute(select(User).order_by(User.full_name))
    return list(result.scalars().all())


async def delete_user(session: AsyncSession, tg_id: int) -> bool:
    """Удаляет пользователя по tg_id и очищает его связанные данные (статусы ДЗ)"""
    user = await get_user_by_tg_id(session, tg_id)
    if not user:
        return False
    await session.execute(delete(UserHomeworkStatus).where(UserHomeworkStatus.user_id == user.id))
    await session.execute(delete(User).where(User.id == user.id))
    await session.commit()
    return True


# ----------------- GROUP CHATS -----------------

async def get_group_chat_by_id(session: AsyncSession, chat_id: int) -> Optional[GroupChat]:
    result = await session.execute(select(GroupChat).where(GroupChat.chat_id == chat_id))
    return result.scalar_one_or_none()


async def create_or_update_group_chat(
    session: AsyncSession,
    chat_id: int,
    title: str,
    chat_type: str = "group",
    added_by: Optional[int] = None,
    role: str = "pending"
) -> GroupChat:
    chat = await get_group_chat_by_id(session, chat_id)
    if chat:
        chat.title = title
        chat.chat_type = chat_type
        if added_by:
            chat.added_by = added_by
    else:
        chat = GroupChat(
            chat_id=chat_id,
            title=title,
            chat_type=chat_type,
            added_by=added_by,
            role=role
        )
        session.add(chat)
    await session.commit()
    await session.refresh(chat)
    return chat


async def update_group_chat_role(session: AsyncSession, chat_id: int, role: str) -> Optional[GroupChat]:
    chat = await get_group_chat_by_id(session, chat_id)
    if chat:
        chat.role = role
        await session.commit()
        await session.refresh(chat)
    return chat


async def get_approved_group_chats(session: AsyncSession) -> List[GroupChat]:
    result = await session.execute(
        select(GroupChat).where(
            GroupChat.role == "approved",
            GroupChat.notifications_enabled == True
        )
    )
    return list(result.scalars().all())


async def get_pending_group_chats(session: AsyncSession) -> List[GroupChat]:
    result = await session.execute(
        select(GroupChat).where(GroupChat.role == "pending").order_by(GroupChat.created_at)
    )
    return list(result.scalars().all())


async def update_group_chat_topic(
    session: AsyncSession,
    chat_id: int,
    topic_type: str,
    thread_id: Optional[int]
) -> Optional[GroupChat]:
    chat = await get_group_chat_by_id(session, chat_id)
    if not chat:
        return None
    if topic_type == "hw":
        chat.topic_hw_id = thread_id
    elif topic_type == "schedule":
        chat.topic_schedule_id = thread_id
    elif topic_type == "duty":
        chat.topic_duty_id = thread_id
    elif topic_type == "announcements":
        chat.topic_announcements_id = thread_id
    elif topic_type == "clear":
        chat.topic_hw_id = None
        chat.topic_schedule_id = None
        chat.topic_duty_id = None
        chat.topic_announcements_id = None
    await session.commit()
    await session.refresh(chat)
    return chat
