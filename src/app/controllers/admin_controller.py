"""Admin endpoints for user and role management."""

from flask import Blueprint, jsonify, request
from bson.errors import InvalidId

from src.app.middlewares.token_required import token_required
from src.app.models.user_model import ALLOWED_ROLES, UserModel
from src.app.services.admin_service import AdminService


class AdminController:
    """User listing and role updates (admin only)."""

    @staticmethod
    @token_required
    def list_users(current_user, token):
        if not current_user.has_role("admin"):
            return jsonify({"error": "Unauthorized"}), 403

        search = request.args.get("search") or request.args.get("q")
        users = UserModel.list_users(search=search.strip() if search else None)
        return jsonify({"users": users}), 200

    @staticmethod
    @token_required
    def get_user_profile(current_user, token, user_id):
        if not current_user.has_role("admin"):
            return jsonify({"error": "Unauthorized"}), 403
        try:
            result = AdminService.get_user_profile(user_id)
        except InvalidId:
            return jsonify({"error": "User not found"}), 404
        except Exception as exc:
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(exc) or "Error loading user profile"}), 500
        if not result:
            return jsonify({"error": "User not found"}), 404
        return jsonify(result), 200

    @staticmethod
    @token_required
    def update_user_roles(current_user, token, user_id):
        if not current_user.has_role("admin"):
            return jsonify({"error": "Unauthorized"}), 403

        data = request.get_json() or {}
        roles = data.get("roles")

        if not isinstance(roles, list) or len(roles) == 0:
            return jsonify({"error": "roles must be a non-empty list"}), 400

        invalid = [role for role in roles if role not in ALLOWED_ROLES]
        if invalid:
            return jsonify({"error": f"Invalid roles: {', '.join(invalid)}"}), 400

        normalized = UserModel.normalize_roles(roles=roles)
        if not normalized:
            return jsonify({"error": "roles must be a non-empty list"}), 400

        if str(current_user._id) == str(user_id) and "admin" not in normalized:
            return jsonify({"error": "You cannot remove your own admin role"}), 400

        try:
            updated = UserModel.update_roles(user_id, normalized)
        except InvalidId:
            return jsonify({"error": "User not found"}), 404

        if not updated:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "_id": updated._id,
            "name": updated.name,
            "email": updated.email,
            "role": updated.role,
            "roles": updated.get_roles(),
        }), 200


admin_blueprint = Blueprint("admin_blueprint", __name__)

admin_blueprint.route("/users", methods=["GET"])(AdminController.list_users)
admin_blueprint.route("/users/<string:user_id>/profile", methods=["GET"])(
    AdminController.get_user_profile
)
admin_blueprint.route("/users/<string:user_id>/roles", methods=["PATCH"])(
    AdminController.update_user_roles
)
