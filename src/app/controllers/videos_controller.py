"""Module for handling videos-related endpoints."""

from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest, Unauthorized
from src.app.services.video_service import VideoService

class VideoController:
    @staticmethod
    def create_video():
        data = request.get_json()
        
        if ("title" or "tuthumbnail" or "deck_id" or "video_id") not in data:
            return BadRequest(description="the fields are mandatory")
        
        result = VideoService.create_video(data)
        return jsonify(result), 201
    
    @staticmethod
    def get_all_videos():
        
        
        result = VideoService.get_all_videos()
        return jsonify(result), 201



video_blueprint = Blueprint("video_blueprint", __name__)

video_blueprint.route("/create", methods=["POST"])(VideoController.create_video)
video_blueprint.route("/get", methods=["GET"])(VideoController.get_all_videos)