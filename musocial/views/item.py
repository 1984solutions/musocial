from flask import Blueprint, jsonify, request
from flask_jwt_extended import current_user

from musocial import models as m
from musocial.main import app, db, jwt_required

item_blueprint = Blueprint('item', __name__)

@item_blueprint.route('/items/<int:item_id>/like', methods=['POST'])
@jwt_required
def like(item_id):
    user_item = m.UserItem.query.filter_by(user=current_user, item_id=item_id).first()
    liked = bool(int(request.form['value']))
    if not user_item:
        if liked: # you could like an item that is not in your feed (if you see it in somebody else's feed)
            user_item = m.UserItem(user=current_user, item_id=item_id)
        else: # unliking a missing item should simply be ignored
            return jsonify(ok=True)
    user_item.liked = liked
    db.session.add(user_item)
    db.session.commit()
    return jsonify(ok=True)

@item_blueprint.route('/items/<int:item_id>/hide', methods=['POST'])
@jwt_required
def hide(item_id):
    user_item = m.UserItem.query.filter_by(user=current_user, item_id=item_id).first()
    user_item.read = bool(int(request.form['value']))
    db.session.add(user_item)
    db.session.commit()
    return jsonify(ok=True)

@item_blueprint.route('/items/<int:item_id>/played-value', methods=['POST'])
@jwt_required
def played_value(item_id):
    # TODO: possible concurrency issue - ideally we use SQL to increment rather than SQLAlchemy
    # but this is probably OK since it refers to one user's item
    user_item = m.UserItem.query.filter_by(user=current_user, item_id=item_id).first()
    # NB: the "value" here refers to the podcast:value interval which is a minute
    # see: https://github.com/Podcastindex-org/podcast-namespace/blob/main/value/value.md#payment-intervals
    user_item.played_value_count += int(request.form['value'])
    db.session.add(user_item)
    db.session.commit()
    return jsonify(ok=True)
