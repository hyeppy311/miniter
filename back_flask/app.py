from flask import Flask, request, jsonify
from flask.json import JSONEncoder

app = Flask(__name__) 
app.id_count = 1
app.users = {}
app.tweets = []

# 파이썬 set을 JSON으로 불러오기
class CustomJSONEncoder(JSONEncoder) :
    def default(self, obj) :
        if isinstance(obj,set) :
            return list(obj) 
        
        return JSONEncoder.default(self,obj)
app.json_encoder = CustomJSONEncoder


@app.route('/ping', methods=['GET'])
def ping() :
    return "pong"


# 회원가입
@app.route("/sign-up", methods=['GET','POST'])
def sign_up():
    new_user                = request.json
    new_user["id"]          = app.id_count
    app.users[app.id_count] = new_user
    app.id_count            = app.id_count + 1
    
    return jsonify(new_user)

# 트윗올리기
@app.route('/tweet', methods = ["GET","POST"])
def tweet() :
    payload         = request.json
    user_id         = int(payload['id'])
    tweet           = payload['tweet']
    
    if user_id not in app.users :
        return '사용자가 존재하지 않습니다', 400
    
    if len(tweet) > 300 :
        return '300자를 초과했습니다', 400
    
    user_id = int(payload['id'])
    app.tweets.append({
        'user_id' : user_id,
        'tweet'   : tweet
    })
    
    return " " , 200

# 팔로우 
@app.route('/follow', methods = ["GET","POST"])
def follow() :
    payload             = request.json
    user_id             = int(payload['id'])
    user_id_to_follow   = int(payload['follow'])
    
    if user_id not in app.users or user_id_to_follow not in app.users :
        return "사용자가 존재하지 않습니다.", 400
    
    user = app.users[user_id]
    user.setdefault('follow', set()).add(user_id_to_follow) 
    
    return jsonify(user)

# 언팔로우  
@app.route('/unfollow', methods = ["GET","POST"])
def unfollow() :
    payload             = request.json
    user_id             = int(payload['id'])
    user_id_to_follow   = int(payload['unfollow'])
    
    if user_id not in app.users or user_id_to_follow not in app.users :
        return "사용자가 존재하지 않습니다.", 400
    
    user = app.users[user_id]
    user.setdefault('follow', set()).discard(user_id_to_follow) 
    
    return jsonify(user)

# 타임라인 불러오기
@app.route('/timeline/<int:user_id>', methods=['GET'])
def timeline(user_id):
    if user_id not in app.users :
        return '사용자가 존재하지 않습니다', 400
    
    follow_list = app.users[user_id].get('follow', set())
    follow_list.add(user_id)
    timeline = [tweet for tweet in app.tweets if tweet['user_id'] in follow_list]
    
    
    return jsonify({
        'user_id' : user_id,
        'timeline' : timeline
    })
    

if __name__ == "__main__":              
    app.run(host="0.0.0.0", port="8080")
    