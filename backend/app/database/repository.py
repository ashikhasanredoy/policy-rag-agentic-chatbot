from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func, delete, update
from backend.app.database.models import User, Policy, PolicyVersion, Conversation, Message, RetrievalLog, Feedback

class PolicyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, category: Optional[str] = None, status: Optional[str] = None) -> List[Policy]:
        query = select(Policy).order_by(Policy.name)
        if category:
            query = query.where(Policy.category == category)
        if status:
            query = query.where(Policy.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, policy_id: int) -> Optional[Policy]:
        result = await self.db.execute(select(Policy).where(Policy.id == policy_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Policy]:
        result = await self.db.execute(select(Policy).where(Policy.name == name))
        return result.scalar_one_or_none()

    async def create(self, policy: Policy) -> Policy:
        self.db.add(policy)
        await self.db.commit()
        await self.db.refresh(policy)
        return policy

    async def update(self, policy_id: int, **kwargs) -> Optional[Policy]:
        query = update(Policy).where(Policy.id == policy_id).values(**kwargs).execution_options(synchronize_session="fetch")
        await self.db.execute(query)
        await self.db.commit()
        return await self.get_by_id(policy_id)

    async def delete(self, policy_id: int) -> bool:
        await self.db.execute(delete(Policy).where(Policy.id == policy_id))
        await self.db.commit()
        return True

    async def add_version(self, version: PolicyVersion) -> PolicyVersion:
        self.db.add(version)
        await self.db.commit()
        await self.db.refresh(version)
        return version

    async def get_versions(self, policy_id: int) -> List[PolicyVersion]:
        result = await self.db.execute(select(PolicyVersion).where(PolicyVersion.policy_id == policy_id).order_by(desc(PolicyVersion.created_at)))
        return list(result.scalars().all())


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_conversation(self, conv: Conversation) -> Conversation:
        self.db.add(conv)
        await self.db.commit()
        await self.db.refresh(conv)
        return conv

    async def get_conversations_by_user(self, user_id: Optional[int]) -> List[Conversation]:
        query = select(Conversation).order_by(desc(Conversation.updated_at))
        if user_id:
            query = query.where(Conversation.user_id == user_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        result = await self.db.execute(select(Conversation).where(Conversation.id == conversation_id))
        return result.scalar_one_or_none()

    async def add_message(self, message: Message) -> Message:
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_messages(self, conversation_id: str) -> List[Message]:
        result = await self.db.execute(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at))
        return list(result.scalars().all())

    async def log_retrieval(self, log: RetrievalLog) -> RetrievalLog:
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def get_recent_logs(self, limit: int = 50) -> List[RetrievalLog]:
        result = await self.db.execute(select(RetrievalLog).order_by(desc(RetrievalLog.created_at)).limit(limit))
        return list(result.scalars().all())

    async def delete_conversation(self, conversation_id: str, user_id: Optional[int] = None) -> bool:
        # Check if conversation exists
        conv = await self.get_conversation(conversation_id)
        if not conv:
            return False
        if user_id and conv.user_id != user_id:
            return False

        # Delete feedback for messages in this conversation
        msg_subq = select(Message.id).where(Message.conversation_id == conversation_id)
        msg_ids_res = await self.db.execute(msg_subq)
        msg_ids = [row[0] for row in msg_ids_res.fetchall()]
        if msg_ids:
            await self.db.execute(delete(Feedback).where(Feedback.message_id.in_(msg_ids)))

        # Delete conversation (messages and retrieval logs cascade automatically)
        await self.db.delete(conv)
        await self.db.commit()
        return True


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
