
from datetime import timedelta
from webbrowser import get
from flask import Flask, current_app, request, jsonify, Response, g 
from flask_cors import CORS
from flask.json import JSONEncoder
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
from db_model import get_user, insert_user,insert_follow, insert_tweet, insert_unfollow,get_timeline,get_user_id_and_password
import jwt
import bcrypt
from functools import wraps


# 파이선의 set을 JSON으로 변환 
class CustomJSONEncoder(JSONEncoder) :
        def default(self, obj) :
            if isinstance(obj,set) :
                return list(obj) 
            
            return JSONEncoder.default(self,obj)

#########################################################
# 인증 decorator
#########################################################

def login_required(f) :
    @wraps(f)
    def decorated_function(*args, **kwargs) :
        access_token = request.headers.get('Authorization')
        if access_token is not None :
            try :
                payload = jwt.decode(access_token, current_app.config['JWT_SECRET_KEY'], "HS256")
            except jwt.InvalidTokenError :
                payload = None
            
            if payload is None: return Response(status=401)
            
            user_id = payload['user_id']
            g.user_id = user_id
            g.user = get_user(user_id if user_id else None)
        else : 
            return Response(status= 401)
        
        return f(*args, **kwargs)
    return decorated_function


#######################################################
# 팩토리함수 & 앤드포인트 
#######################################################
def create_app(test_config = None) :
    
    app = Flask(__name__)
    
    CORS(app)
    app.json_encoder = CustomJSONEncoder
    
    
    if test_config is None :
        app.config.from_pyfile("config.py")
    else : 
        app.config.update(test_config)
    
    database = create_engine(app.config['DB_URL'], encoding = 'utf-8', max_overflow = 0)
    app.database = database
    
    
    # 핑퐁
    @app.route('/ping', methods = ['GET'])
    def ping() : 
        return 'pong'
    
    
    # 회원가입
    @app.route("/sign-up", methods=['GET','POST'])
    def sign_up():
        new_user         = request.json
        new_user['password'] = bcrypt.hashpw(
                                new_user['password'].encode('UTF-8'),
                                bcrypt.gensalt()
                             ).decode()

        
        new_user_id             = insert_user(new_user)
        new_user                = get_user(new_user_id)
        
        return jsonify(new_user)
    
    # 로그인 인증 
    @app.route('/login', methods=["POST"])
    def login():
        credential      = request.json
        email           = credential['email']
        password        = credential['password']
        user_credential = get_user_id_and_password(email)
        
        if user_credential and bcrypt.checkpw(password.encode('UTF-8'),
                    user_credential['hashed_password'].encode('UTF-8')) :
            user_id = user_credential['id']
            payload = {
                'user_id' : user_id,
                'exp'     : datetime.utcnow() + timedelta(seconds= 60*60*24)
            }
            token = jwt.encode(payload, app.config['JWT_SECRET_KEY'],'HS256')
        
            return jsonify({
                'access_token' : token
        })
        else : 
            return " ", 401
        
    # 트윗올리기
    @app.route('/tweet', methods = ["GET","POST"])
    @login_required
    def tweet() :
        user_tweet      = request.json
        user_tweet['id'] = g.user_id
        tweet           = user_tweet['tweet']
        
        if len(tweet) > 300 :
            return '300자를 초과했습니다', 400
        
        insert_tweet(user_tweet)
        
        return " " , 200
    
    
    # 팔로우 
    @app.route('/follow', methods = ["GET","POST"])
    @login_required
    def follow() :
        payload             = request.json
        payload             = g.user_id
        
        insert_follow(payload)
        
        return ' ', 200

    # 언팔로우  
    @app.route('/unfollow', methods = ["GET","POST"])
    @login_required  
    def unfollow() :
        payload             = request.json
        payload             = g.user_id
        
        insert_unfollow(payload)
        
        return " ", 200

    # 타임라인 불러오기
    @app.route('/timeline/<int:user_id>', methods=['GET'])
    def timeline(user_id):
        return jsonify({
            'user_id'  : user_id,
            'timeline' : get_timeline(user_id)
        })
    @app.route('/timeline', methods=['GET'])
    @login_required
    def user_timeline() :
        user_id = g.user_id
        
        return jsonify({
            'user_id' : user_id,
            'timeline' : get_timeline(user_id)
        })

    
    
    return app 

if __name__ == "__main__":   
    app = create_app()           
    app.run(debug=True)



# @app.route('/ping', methods=['GET'])
# def ping() :
#     return "pong"


# # 회원가입
# @app.route("/sign-up", methods=['GET','POST'])
# def sign_up():
#     new_user                = request.json
#     new_user["id"]          = app.id_count
#     app.users[app.id_count] = new_user
#     app.id_count            = app.id_count + 1
    
#     return jsonify(new_user)

# # 트윗올리기
# @app.route('/tweet', methods = ["GET","POST"])
# def tweet() :
#     payload         = request.json
#     user_id         = int(payload['id'])
#     tweet           = payload['tweet']
    
#     if user_id not in app.users :
#         return '사용자가 존재하지 않습니다', 400
    
#     if len(tweet) > 300 :
#         return '300자를 초과했습니다', 400
    
#     user_id = int(payload['id'])
#     app.tweets.append({
#         'user_id' : user_id,
#         'tweet'   : tweet
#     })
    
#     return " " , 200

# # 팔로우 
# @app.route('/follow', methods = ["GET","POST"])
# def follow() :
#     payload             = request.json
#     user_id             = int(payload['id'])
#     user_id_to_follow   = int(payload['follow'])
    
#     if user_id not in app.users or user_id_to_follow not in app.users :
#         return "사용자가 존재하지 않습니다.", 400
    
#     user = app.users[user_id]
#     user.setdefault('follow', set()).add(user_id_to_follow) 
    
#     return jsonify(user)

# # 언팔로우  
# @app.route('/unfollow', methods = ["GET","POST"])
# def unfollow() :
#     payload             = request.json
#     user_id             = int(payload['id'])
#     user_id_to_follow   = int(payload['unfollow'])
    
#     if user_id not in app.users or user_id_to_follow not in app.users :
#         return "사용자가 존재하지 않습니다.", 400
    
#     user = app.users[user_id]
#     user.setdefault('follow', set()).discard(user_id_to_follow) 
    
#     return jsonify(user)

# # 타임라인 불러오기
# @app.route('/timeline/<int:user_id>', methods=['GET'])
# def timeline(user_id):
#     if user_id not in app.users :
#         return '사용자가 존재하지 않습니다', 400
    
#     follow_list = app.users[user_id].get('follow', set())
#     follow_list.add(user_id)
#     timeline = [tweet for tweet in app.tweets if tweet['user_id'] in follow_list]
    
    
#     return jsonify({
#         'user_id' : user_id,
#         'timeline' : timeline
#     })
    
# @app.route('/timeline/<int:user_id>', methods=['GET'])
# def timeline(user_id):
#     return jsonify({
#         'user_id' : user_id,
#         'timeline' : get_timeline(user_id)

# if __name__ == "__main__":              
#     app.run(host="0.0.0.0", port="8080")
    