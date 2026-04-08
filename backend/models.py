from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.sql import func
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "lantunes.db")
DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Artist(Base):
    __tablename__ = "artists"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    sort_name = Column(String(255))
    artwork_path = Column(String(500))
    created_at = Column(DateTime, default=func.now())
    albums = relationship("Album", back_populates="artist")

class Album(Base):
    __tablename__ = "albums"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    artist_id = Column(Integer, ForeignKey("artists.id"))
    year = Column(Integer)
    genre = Column(String(100))
    artwork_path = Column(String(500))
    created_at = Column(DateTime, default=func.now())
    artist = relationship("Artist", back_populates="albums")
    tracks = relationship("Track", back_populates="album")

class Track(Base):
    __tablename__ = "tracks"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    album_id = Column(Integer, ForeignKey("albums.id"))
    artist_id = Column(Integer, ForeignKey("artists.id"))
    disc_number = Column(Integer, default=1)
    track_number = Column(Integer)
    duration = Column(Integer)
    path = Column(String(500), unique=True)
    file_format = Column(String(20))
    bitrate = Column(Integer)
    sample_rate = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    album = relationship("Album", back_populates="tracks")
    
    def as_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "album_id": self.album_id,
            "artist_id": self.artist_id,
            "disc_number": self.disc_number,
            "track_number": self.track_number,
            "duration": self.duration,
            "path": self.path,
            "file_format": self.file_format,
            "bitrate": self.bitrate,
            "sample_rate": self.sample_rate
        }

class Playlist(Base):
    __tablename__ = "playlists"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"
    id = Column(Integer, primary_key=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id", ondelete="CASCADE"))
    track_id = Column(Integer, ForeignKey("tracks.id", ondelete="CASCADE"))
    position = Column(Integer, nullable=False)

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    client_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100))
    client_type = Column(String(20))
    last_seen = Column(DateTime, default=func.now())
    is_controller = Column(Boolean, default=True)

class PlaybackState(Base):
    __tablename__ = "playback_state"
    id = Column(Integer, primary_key=True, default=1)
    current_track_id = Column(Integer, ForeignKey("tracks.id"))
    position = Column(Integer, default=0)
    is_playing = Column(Boolean, default=False)
    volume = Column(Float, default=1.0)
    queue = Column(Text, nullable=True)  # Stored as comma-separated track IDs
    shuffle_mode = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user")  # "admin" or "user"
    status = Column(String(20), default="pending")  # "pending", "active", "inactive"
    created_at = Column(DateTime, default=func.now())
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()