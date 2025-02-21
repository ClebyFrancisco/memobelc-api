from src.app.models.video_model import VideoModel
from datetime import datetime, timezone

class VideoService:
    @staticmethod
    def create_video(data):
        """Cria um novo video e o salva no banco de dados."""
        video = VideoModel(
            title=data.get("title"), 
            thumbnail=data.get("thumbnail"), 
            deck_id=data.get("deck_id"), 
            video_id=data.get("video_id")
        )
        video.save_to_db()
        return video.to_dict()
    
    @staticmethod
    def get_all_videos():
        return VideoModel.get_all_videos()
    
    
    
    