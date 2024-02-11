from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import LoginManager,login_required,current_user
import os

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
#Access-Control-Allow-Credentials
ALLOWED_ORIGINS = ['http://example.com']
@app.after_request
def after_request_func(response):
    origin = request.headers.get('Origin')
    if origin in ALLOWED_ORIGINS:
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response
#ユーザー
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(25))
#住所情報
class Point(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(140), nullable=False)
    latitude = db.Column(db.Float(140), nullable=False)
    longitude = db.Column(db.Float(140), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#経路情報
class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_point = db.Column(db.String(128), nullable=False)
    end_point = db.Column(db.String(128), nullable=False)
    start_point_id = db.Column(db.Integer, db.ForeignKey('point.id'), nullable=False)  
    end_point_id = db.Column(db.Integer, db.ForeignKey('point.id'), nullable=False)  
    waypoints = db.relationship('Waypoint', backref='route', lazy=True)
    favorited = db.Column(db.Boolean, default=False)
    start_location = db.relationship('Point', foreign_keys=[start_point_id], uselist=False, backref='route_start')
    end_location = db.relationship('Point', foreign_keys=[end_point_id], uselist=False, backref='route_end')
class Waypoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('route.id'), nullable=False)
    waypoint = db.Column(db.String(128), nullable=False)
    waypoint_id = db.Column(db.Integer, db.ForeignKey('point.id'), nullable=False) 
    way_location = db.relationship('Point', foreign_keys=[waypoint_id], uselist=False, backref='route_way')
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
#ユーザー登録
@app.route('/users',methods=['POST'])
def create_user():
    data=request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')
    user=User(username=data['username'],password=hashed_password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'id':user.id,'username':user.username}),201

@app.route('/users',methods=['GET'])
@login_required
def get_user(user_id):
    user=User.query.get_or_404(user_id)
    return jsonify({'username':user.username,
                    'password':user.password})
@app.route('/users/<int:user_id>',methods=['PUT'])
@login_required
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        abort(404)  
    data = request.get_json()
    if 'username' in data:
        user.username=data['username']
    if 'password' in data:
        user.password=generate_password_hash(data['password'], method='sha256')
    db.session.commit()
    return jsonify({'id': user.id, 'username': user.username}), 200
#住所登録
@app.route('/points',methods=['POST'])
@login_required
def create_point():
    data=request.get_json()
    point=Point(name=data['name'],adress=data['address'],user_id=data['user_id'],latitude=data['latitude'],longitude=data['longitude'])
    db.session.add(point)
    db.session.commit()
    return jsonify({
        'id':point.id,
        'name':point.name,
        'address':point.adress,
        'latitude':point.latitude,
        'longitude':point.longitude,
        'user_id':point.user_id
        }),201

@app.route('/points',methods=['GET'])
@login_required
def get_point(user_id):
    point=Point.query.filter_by(user_id=user_id).all()
    point_data=[{
        'id': point.id,
        'name':point.name,
        'address':point.adress,
        'latitude':point.latitude,
        'longitude':point.longitude,
        'user_id':point.user_id,
    } for point in point]
    return jsonify(point_data),200

@app.route('/points/<int:points_id>',methods=['PUT'])
@login_required
def update_point(point_id):
    point = Point.query.get(point_id)
    if not point:
        abort(404)  
    data = request.get_json()
    point.name=data.get('name',point.name)
    point.adress=data.get('address',point.adress)
    db.session.commit()
    return jsonify({
        'id': point.id, 
        'name': point.name,
        'address':point.adress,
        'latitude':point.latitude,
        'longitude':point.latitude,
        'user_id':point.user_id}), 200
    
@app.route('/points/<int:points_id>', methods=['DELETE'])
@login_required
def delete_point(point_id):
    point = Point.query.get(point_id)
    if not point:
        abort(404)  
    db.session.delete(point)
    db.session.commit()
    return jsonify({'message': ' 登録情報は削除されました'}), 200
#経路登録
@app.route('/routes',methods=['POST'])
@login_required
def create_route():
    data=request.get_json()
    user_id=current_user.id
    start_point=data['start_point']
    end_point=data['end_point']
    waypoints=data.get('waypoint',[])
    route=Route(user_id=user_id,start_point=start_point,end_point=end_point)
    db.session.add(route)
    db.session.flush()
    for waypoint_data in waypoints:
        point=Point(
            name=waypoint_data['name'],
            address=waypoint_data['address'],
            latitude=waypoint_data['latitude'], 
            longitude=waypoint_data['longitude'],
            user_id=user_id
        )
        db.session.add(waypoint)
    db.session.commit()
    return jsonify({'route_id':route.id,'waypoints':len(waypoints)}),201

@app.route('/routes',methods=['GET'])
@login_required
def get_route(route_id):
    route=Route.query.get_or_404(route_id)
    db.session.refresh(route)
    waypoints = Waypoint.query.filter_by(route_id=route.id).all()
    waypoints_data = [{'id': wp.id, 'location': wp.location} for wp in waypoints]
    return jsonify({
        'id': route.id,
        'user_id':route.user_id,
        'start_point':route.start_point,
        'end_point':route.end_point,
        'waypoint':waypoints_data})

@app.route('/routes/<int:route_id>', methods=['PUT'])
@login_required
def update_route(route_id):
    route = Route.query.get_or_404(route_id)
    data = request.get_json()
    route.start_point = data.get('start_point', route.start_point)
    route.end_point = data.get('end_point', route.end_point)
    db.session.commit()
    return jsonify({'id':route.id,
                    'user_id':route.user_id,
                    'start_point':route.start_point,
                    'end_point':route.end_point
                    }), 200
    
@app.route('/waypoints/<int:waypoint_id>', methods=['PUT'])
@login_required
def update_waypoint(waypoint_id):
    waypoint = Waypoint.query.get_or_404(waypoint_id)
    data = request.get_json()
    waypoint.location = data.get('location', waypoint.location)
    
    db.session.commit()
    return jsonify({'waypoint':waypoint}), 200

@app.route('/routes/<int:route_id>', methods=['DELETE'])
@login_required
def delete_route(route_id):
    route = Route.query.get_or_404(route_id)
    db.session.delete(route)
    db.session.commit()
    return jsonify({'message': '削除に成功しました'}), 200

@app.route('/waypoints/<int:waypoint_id>', methods=['DELETE'])
@login_required
def delete_waypoint(waypoint_id):
    waypoint = Waypoint.query.get_or_404(waypoint_id)
    db.session.delete(waypoint)
    db.session.commit()
    return jsonify({'message': '削除に成功しました'}), 200
#お気に入り登録、解除
@app.route('/routes/<int:route_id>/favorite', methods=['POST'])
@login_required
def favorite_route(route_id):
    route = Route.query.get_or_404(route_id)
    user_id = request.json.get('user_id')
    if route.favorited:
        return jsonify({'message': '既にお気に入り登録しています。'}), 400
    route.user_id = user_id
    db.session.commit()
    return jsonify({'message': 'Route favorited successfully'}), 200

@app.route('/routes/<int:route_id>/unfavorite', methods=['POST'])
@login_required
def unfavorite_route(route_id):
    route = Route.query.get_or_404(route_id)
    if not route.favorited:
        return jsonify({'message': 'お気に入りに登録されていません。'}), 400
    route.user_id = None
    db.session.commit()
    return jsonify({'message': 'お気に入りを解除しました。'}), 200

@app.route('/user/<int:user_id>/favorited_routes', methods=['GET'])
@login_required
def get_favorited_routes(user_id):
    favorited_routes = Route.query.filter_by(user_id=user_id, favorited=True).all()
    data = [{
        'id': route.id,
        'user_id': route.user_id,
        'start_point': route.start_point,
        'end_point': route.end_point,
        'favorited': route.favorited
    } for route in favorited_routes]

    return jsonify(data), 200
if __name__ == "__main__":
    app.run(debug=True)