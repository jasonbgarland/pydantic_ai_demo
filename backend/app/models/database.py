"""SQLAlchemy models for PostgreSQL persistence."""
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, DateTime, JSON, ForeignKey, Boolean, Text, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Character(Base):
    """Persistent character model for saved games."""
    __tablename__ = "characters"

    id = Column(String, primary_key=True)  # UUID
    name = Column(String, nullable=False)
    character_class = Column(String, nullable=False)  # warrior, wizard, rogue
    stats = Column(JSON, nullable=False)  # {strength, magic, agility, health, stealth}
    level = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    game_sessions = relationship("GameSession", back_populates="character")

    def __repr__(self):
        return f"<Character(id={self.id}, name={self.name}, class={self.character_class})>"


class GameSession(Base):
    """Saved game session with full state."""
    __tablename__ = "game_sessions"

    id = Column(String, primary_key=True)  # UUID
    character_id = Column(String, ForeignKey("characters.id"), nullable=False)

    # Game state
    current_location = Column(String, nullable=False)
    inventory = Column(JSON, default=list)  # List of item names
    turn_count = Column(Integer, default=0)

    # Session metadata
    session_name = Column(String, nullable=True)  # User-friendly save name
    is_active = Column(Boolean, default=True)  # Current session vs archived save
    last_played = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Full state snapshot (for Redis compatibility)
    state_snapshot = Column(JSON, nullable=True)  # Complete session state

    # Relationships
    character = relationship("Character", back_populates="game_sessions")
    discoveries = relationship("Discovery", back_populates="game_session")
    narrative_entries = relationship("NarrativeHistory", back_populates="game_session")

    # Index for fast lookups
    __table_args__ = (
        Index('idx_character_active', 'character_id', 'is_active'),
    )

    def __repr__(self):
        return f"<GameSession(id={self.id}, character={self.character_id}, location={self.current_location})>"


class Discovery(Base):
    """Track player discoveries for achievements and world state."""
    __tablename__ = "discoveries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_session_id = Column(String, ForeignKey("game_sessions.id"), nullable=False)

    # Discovery type and details
    discovery_type = Column(String, nullable=False)  # room, item, secret, npc, etc.
    entity_id = Column(String, nullable=False)  # cave_entrance, magical_rope, etc.
    display_name = Column(String, nullable=False)  # Cave Entrance, Magical Rope

    # Metadata
    discovered_at = Column(DateTime, default=datetime.utcnow)
    turn_number = Column(Integer, nullable=False)  # Which turn was this discovered
    context = Column(JSON, nullable=True)  # Optional: how it was discovered

    # Relationships
    game_session = relationship("GameSession", back_populates="discoveries")

    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_session_type', 'game_session_id', 'discovery_type'),
        Index('idx_session_entity', 'game_session_id', 'entity_id'),
    )

    def __repr__(self):
        return f"<Discovery(type={self.discovery_type}, entity={self.entity_id})>"


class NarrativeHistory(Base):
    """Complete conversation history for replay and analysis."""
    __tablename__ = "narrative_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_session_id = Column(String, ForeignKey("game_sessions.id"), nullable=False)

    # Turn information
    turn_number = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Command and response
    command = Column(Text, nullable=False)  # User input
    narrative = Column(Text, nullable=False)  # AI response

    # Agent metadata (optional)
    agent_used = Column(String, nullable=True)  # Which agent generated response
    response_metadata = Column(JSON, nullable=True)  # Timing, tokens, etc.

    # Relationships
    game_session = relationship("GameSession", back_populates="narrative_entries")

    # Index for chronological queries
    __table_args__ = (
        Index('idx_session_turn', 'game_session_id', 'turn_number'),
    )

    def __repr__(self):
        return f"<NarrativeHistory(session={self.game_session_id}, turn={self.turn_number})>"
