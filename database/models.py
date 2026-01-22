# Database models for PostgreSQL using SQLAlchemy
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True)
    level = Column(String(50), default='intermediate')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sessions = relationship('Session', back_populates='user')
    progress = relationship('UserProgress', back_populates='user', uselist=False)
    vocabulary = relationship('Vocabulary', back_populates='user')
    grammar_errors = relationship('GrammarError', back_populates='user')


class Session(Base):
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    mode = Column(String(20), default='tutor')
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)

    user = relationship('User', back_populates='sessions')
    conversations = relationship('Conversation', back_populates='session')


class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('sessions.id'))
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship('Session', back_populates='conversations')
    grammar_errors = relationship('GrammarError', back_populates='conversation')


class GrammarError(Base):
    __tablename__ = 'grammar_errors'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    original_text = Column(Text, nullable=False)
    corrected_text = Column(Text, nullable=False)
    error_type = Column(String(100))
    explanation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='grammar_errors')
    conversation = relationship('Conversation', back_populates='grammar_errors')


class UserProgress(Base):
    __tablename__ = 'user_progress'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    total_sessions = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    errors_corrected = Column(Integer, default=0)
    vocabulary_learned = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_practice_date = Column(Date)

    user = relationship('User', back_populates='progress')


class Vocabulary(Base):
    __tablename__ = 'vocabulary'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    word = Column(String(255), nullable=False)
    definition = Column(Text)
    example_sentence = Column(Text)
    mastery_level = Column(Integer, default=0)
    last_reviewed = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='vocabulary')


class APIKeyUsage(Base):
    """Track API key usage for rotation"""
    __tablename__ = 'api_key_usage'

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_index = Column(Integer, nullable=False)
    request_count = Column(Integer, default=0)
    last_used = Column(DateTime)
    last_error = Column(DateTime)
    error_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_database_url():
    """Get database URL from environment"""
    # Railway provides DATABASE_URL automatically
    database_url = os.getenv('DATABASE_URL')

    if database_url:
        # Railway uses postgres:// but SQLAlchemy needs postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        return database_url

    # Fallback to SQLite for local development
    return 'sqlite:///tutor.db'


def get_engine():
    """Create and return database engine"""
    database_url = get_database_url()
    return create_engine(database_url, pool_pre_ping=True)


def get_session():
    """Create and return a database session"""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_database():
    """Initialize database tables"""
    engine = get_engine()
    Base.metadata.create_all(engine)
    print("Database tables created successfully")


if __name__ == '__main__':
    init_database()
