from flask import Blueprint, request, jsonify

from ..utils.jwt_handler import JWTManager
from ..services.notification_service_impl import NotificationService
from ..exceptions.auth_exceptions import NoSuchUserException
# from ..exceptions.auction_exceptions import AuctionNotFoundException


def init_notification_routes(notification_service: NotificationService, jwt_manager: JWTManager):
    notification_bp = Blueprint('notification', __name__, url_prefix='/api/notifications')

    @notification_bp.route('', methods=['GET'])
    @jwt_manager.token_required
    def get_notifications(user_id):
        try:
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('pageSize', 10))

            response = notification_service.get_user_notifications(
                user_id=user_id,
                page=page,
                page_size=page_size
            )

            result = {
                'notifications': [notification.__dict__ for notification in response.notifications],
                'unread_count': response.unread_count
            }

            return jsonify(result), 200
        except NoSuchUserException as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @notification_bp.route('/<notification_id>/read', methods=['PATCH'])
    @jwt_manager.token_required
    def mark_as_read(user_id, notification_id):
        try:
            success = notification_service.mark_as_read(
                notification_id=notification_id,
                user_id=user_id
            )

            if success:
                return jsonify({'message': 'Notification marked as read'}), 200
            else:
                return jsonify({'error': 'Notification not found or not owned by user'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @notification_bp.route('/read-all', methods=['PATCH'])
    @jwt_manager.token_required
    def mark_all_as_read(user_id):
        try:
            count = notification_service.mark_all_as_read(user_id)
            return jsonify({
                'message': f'Marked {count} notifications as read',
                'count': count
            }), 200
        except NoSuchUserException as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @notification_bp.route('/<notification_id>', methods=['DELETE'])
    @jwt_manager.token_required
    def delete_notification(user_id, notification_id):
        try:
            user_notifications = notification_service.get_user_notifications(user_id)
            notification_ids = [n.id for n in user_notifications.notifications]

            if notification_id not in notification_ids:
                return jsonify({'error': 'Notification not found or not owned by user'}), 404

            success = notification_service.notification_repository.delete(notification_id)

            if success:
                return jsonify({'message': 'Notification deleted'}), 200
            else:
                return jsonify({'error': 'Failed to delete notification'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return notification_bp