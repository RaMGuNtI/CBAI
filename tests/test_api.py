import pytest
from app.database.connection import SessionLocal, init_db
from app.backend.schemas.chatbot import ChatbotCreate, PublishStatusUpdate
from app.backend.schemas.chat import ChatRequest
from app.backend.schemas.auth import UserRegister, UserLogin
from app.backend.routes import auth, chatbots, chat, public, analytics
from app.backend.main import health_check


@pytest.fixture(scope="module")
def db_session():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_health_check_endpoint():
    res = health_check()
    assert res["status"] == "healthy"
    assert "CustomBot AI" in res["service"]


def test_auth_endpoints(db_session):
    import uuid
    uid = uuid.uuid4().hex[:8]
    # Test registration
    reg_data = UserRegister(
        email=f"test_{uid}@example.com",
        username=f"user_{uid}",
        password="SecurePassword123!"
    )
    user_resp = auth.register(reg_data, db=db_session)
    assert user_resp.email == f"test_{uid}@example.com"
    assert user_resp.username == f"user_{uid}"

    # Test login
    login_data = UserLogin(
        username_or_email=f"user_{uid}",
        password="SecurePassword123!"
    )
    token_resp = auth.login(login_data, db=db_session)
    assert token_resp.access_token is not None
    assert token_resp.user_id == user_resp.id


def test_chatbot_lifecycle_and_chat(db_session):
    # 1. Create Bot
    create_data = ChatbotCreate(
        name="API Test Support Bot",
        description="Testing direct API routing and database persistence",
        purpose="Support users with return queries",
        welcome_message="Hello from test bot!",
        domain="Customer Support"
    )
    created_bot = chatbots.create_chatbot(create_data, db=db_session)
    assert created_bot.name == "API Test Support Bot"
    bot_id = created_bot.id
    share_token = created_bot.share_token

    # 2. Get Bot
    fetched = chatbots.get_chatbot(bot_id, db=db_session)
    assert fetched.id == bot_id
    assert fetched.domain == "Customer Support"

    # 3. Chat with Bot (triggers strict fallback when no documents uploaded)
    chat_req = ChatRequest(
        message="What is the shipping cost to Mars?",
        session_id="test_session_api_1"
    )
    chat_resp = chat.chat_with_bot(bot_id, chat_req, db=db_session)
    assert "could not find relevant information" in chat_resp.answer.lower()
    assert len(chat_resp.sources) == 0

    # 4. Publish Bot
    pub_update = PublishStatusUpdate(is_published=True)
    published = chatbots.set_publish_status(bot_id, pub_update, db=db_session)
    assert published.is_published is True

    # 5. Public Endpoint Access
    pub_info = public.get_public_chatbot(share_token, db=db_session)
    assert pub_info["name"] == "API Test Support Bot"
    assert "share_token" in pub_info

    # 6. Analytics Dashboard
    metrics = analytics.get_dashboard_metrics(db=db_session)
    assert metrics.total_chatbots >= 1
    assert metrics.total_conversations >= 1

    # 7. Delete Bot
    del_res = chatbots.delete_chatbot(bot_id, db=db_session)
    assert del_res["message"] == "Chatbot deleted successfully"
