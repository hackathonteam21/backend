from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash,check_password_hash
import os
app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
#ユーザー
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(25))
#住所情報
class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    adress = db.Column(db.String(140), nullable=False)
    latitude = db.Column(db.String(140), nullable=False)
    longitude = db.Column(db.String(140), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#経路情報
class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_point = db.Column(db.String(128), nullable=False)
    end_point = db.Column(db.String(128), nullable=False)
    waypoints = db.relationship('Waypoint', backref='route', lazy=True)
    favorited_by = db.relationship('User', backref='favorited_route', uselist=False)
class Waypoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('route.id'), nullable=False)
    location = db.Column(db.String(128), nullable=False)
#ユーザー登録
@app.route('/users',methods=['POST'])
def create_user():
    data=request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')
    user=User(username=data['username'],password=hashed_password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'id':user.id,'username':user.username}),201

@app.route('/user/<int:user_id>',methods={'GET'})
def get_user(user_id):
    user=User.query.get_or_404(user_id)
    return jsonify({'username':user.username,'password':user.password})
@app.route('/users/<int:user_id>',methods=['PUT'])
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
@app.route('/tweets',methods=['POST'])
def create_tweet():
    data=request.get_json()
    tweet=Tweet(name=data['name'],adress=data['adress'],user_id=data['user_id'],latitude=data['latitude'],longitude=data['longitude'])
    db.session.add(tweet)
    db.session.commit()
    return jsonify({
        'id':tweet.id,
        'name':tweet.name,
        'adress':tweet.adress,
        'latitude':tweet.latitude,
        'longitude':tweet.latitude,
        'user_id':tweet.user_id
        }),201

@app.route('/tweets/<int:tweets_id>',methods=['GET'])
def get_tweet(tweet_id):
    tweet=Tweet.query.get_or_404(tweet_id)
    return jsonify({
        'id': tweet.id,
        'name':tweet.name,
        'adress':tweet.adress,
        'latitude':tweet.latitude,
        'longitude':tweet.latitude,
        'user_id':tweet.user_id,
        })

@app.route('/tweets/<int:tweets_id>',methods=['PUT'])
def update_tweet(tweet_id):
    tweet = Tweet.query.get(tweet_id)
    if not tweet:
        abort(404)  
    data = request.get_json()
    tweet.name=data.get('name',tweet.name)
    tweet.adress=data.get('adress',tweet.adress)
    db.session.commit()
    return jsonify({
        'id': tweet.id, 
        'name': tweet.name,
        'adress':tweet.adress,
        'latitude':tweet.latitude,
        'longitude':tweet.latitude,
        'user_id':tweet.user_id}), 200
    
@app.route('/tweets/<int:tweets_id>', methods=['DELETE'])
def delete_tweet(tweet_id):
    tweet = User.query.get(tweet_id)
    if not tweet:
        abort(404)  
    db.session.delete(tweet)
    db.session.commit()
    return jsonify({'message': ' 登録情報は削除されました'}), 200
#経路登録
@app.route('/routes',methods=['POST'])
def create_route():
    data=request.get_json()
    user_id=data['user_id']
    start_point=data['start_point']
    end_point=data['end_point']
    waypoints=data.get('waypoint',[])
    route=Route(user_id=user_id,start_point=start_point,end_point=end_point)
    db.session.add(route)
    db.session.flush()
    for waypoint_data in waypoints:
        waypoint=Waypoint(route_id=route.id,location=waypoint_data['location'])
        db.session.add(waypoint)
    db.session.commit()
    return jsonify({'route_id':route.id,'waypoints':len(waypoints)}),201

@app.route('/routes/<int:route_id>',methods=['GET'])
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
def update_waypoint(waypoint_id):
    waypoint = Waypoint.query.get_or_404(waypoint_id)
    data = request.get_json()
    waypoint.location = data.get('location', waypoint.location)
    
    db.session.commit()
    return jsonify({'waypoint':waypoint}), 200

@app.route('/routes/<int:route_id>', methods=['DELETE'])
def delete_route(route_id):
    route = Route.query.get_or_404(route_id)
    db.session.delete(route)
    db.session.commit()
    return jsonify({'message': '削除に成功しました'}), 200

@app.route('/waypoints/<int:waypoint_id>', methods=['DELETE'])
def delete_waypoint(waypoint_id):
    waypoint = Waypoint.query.get_or_404(waypoint_id)
    db.session.delete(waypoint)
    db.session.commit()
    return jsonify({'message': '削除に成功しました'}), 200
#お気に入り登録、解除
@app.route('/routes/<int:route_id>/favorite', methods=['POST'])
def favorite_route(route_id):
    route = Route.query.get_or_404(route_id)
    user_id = request.json.get('user_id')
    if route.favorited_by:
        return jsonify({'message': '既にお気に入り登録しています。'}), 400
    route.user_id = user_id
    db.session.commit()
    return jsonify({'message': 'Route favorited successfully'}), 200

@app.route('/routes/<int:route_id>/unfavorite', methods=['POST'])
def unfavorite_route(route_id):
    route = Route.query.get_or_404(route_id)
    if not route.favorited_by:
        return jsonify({'message': 'お気に入りに登録されていません。'}), 400
    route.user_id = None
    db.session.commit()
    return jsonify({'message': 'お気に入りを解除しました。'}), 200
if __name__ == "__main__":
    app.run(debug=True)