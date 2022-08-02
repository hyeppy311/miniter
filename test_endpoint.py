import pytest
import config
import json
import bcrypt

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from app import create_app  # 테스트 할 플라스크앱 호출


database  = create_engine(config.test_config['DB_URL'],
                          encoding = 'utf-8', max_overflow = 0)


@pytest.fixture
def api() : 
    app = create_app(config.test_config)
    app.config['TEST'] = True
    api = app.test_client()
    
    return api

def setup_function() :
    ## test 유저 생성
    
    hashed_password = bcrypt.hashpw(
    b"test password",
    bcrypt.gensalt()
)
    
    new_users=[
        {
            'id' : 3,
            'name' : 'thor',
            'email' : 'thunder@gmail.com',
            'profile' : 'test profile',
            'hashed_password' : hashed_password 
        },
        {
            'id' : 4,
            'name' : '김파이',
            'email' : 'kimpy@gmail.com',
            'profile' : 'test profile',
            'hashed_password' : hashed_password
        }
    ]
    
    database.execute(text("""
            INSERT INTO users(
                id,
                name,
                email,
                profile,
                hashed_password
            ) VALUES(
                :id,
                :name,
                :email,
                :profile,
                :hashed_password
        ) 
        """), new_users)
    
    #user 2 트윗 미리 생성
    database.execute(text("""
                        INSERT INTO tweets(
                            user_id,
                            tweet
                        ) VALUES(
                            2,
                            "Hello world!"
                        )
                        """))
    
def teardown_function() :
    database.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    database.execute(text("TRUNCATE users"))
    database.execute(text("TRUNCATE tweets"))
    database.execute(text("TRUNCATE users_follow_list"))
    database.execute(text("SET FOREIGN_KEY_CHECKS=1"))

def test_ping(api) :
    resp = api.get('/ping')
    assert b'pong' in resp.data

def test_login(api) :
    resp = api.post(
        '/login',
        data = json.dumps({'email' : 'thunder@gmail.com','password' : 'test password'}),
        content_type = 'application/json'
    )
    assert b"access_token" in resp.data

# access token 없이는 401 응답을 리턴하는지 확인
def test_unauthorized(api):
    resp = api.post(
        '/tweet',
        data  = json.dumps({'tweet' : "Hello world!"}),
        content_type = 'application/json'
    )
    assert resp.status_code == 401
    
    resp = api.post(
        '/follow',
        data = json.dumps({'follow' : 2}),
        content_type = 'application/json'
    )
    assert resp.status_code == 401
    
    resp  = api.post(
        '/unfollow',
        data         = json.dumps({'unfollow' : 2}),
        content_type = 'application/json'
    )
    assert resp.status_code == 401


# POST 요청 test 
def test_tweet(api):
    #테스트 사용자 생성
    # new_user = {
    #     'email' : 'thunder@gmail.com',
    #     'password' : 'abc1234',
    #     'name' : 'thor',
    #     'profile' : 'test profile'
    # }
    # resp = api.post(
    #     '/sign-up',
    #     data = json.dumps(new_user),
    #     content_type = 'application/json'
    # )
    # assert resp.status_code == 200 
    
    # # new user 에서 id 가져오기
    # resp_json = json.loads(resp.data.edcode('utf-8'))
    # new_user_id = resp_json['id']
    
    # 로그인
    resp = api.post(
        '/login',
        data = json.dumps({'email' : 'thunder@gmail.com', 'password' : 'test password'}),
        content_type = 'application/json'
    )
    resp_json = json.loads(resp.data.decode('utf-8'))
    access_token = resp_json['access_token']
    
    # tweet
    resp = api.post(
        '/tweet',
        data = json.dumps({'tweet' : "Hello Wolrd!"}),
        content_type = 'application/json',
        headers = {'Authorization' : access_token}
    )
    assert resp.status_code == 200
    
    # tweet 확인
    # resp = api.get(f'/timeline/{new_user_id}')
    resp = api.get(f'/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))
    
    assert resp.status_code == 200 
    assert tweets     == {
        'user_id' : 1,
        'timeline' : [
            {
                'user_id' : 1,
                'tweet'  : "Hello world!"
            }
        ]
    }

def test_follow(api) : 
    # 로그인
    resp = api.post(
        '/login', 
        data = json.dumps({'email': 'thunder@gmail.com', 'password' : 'test password'}),
        content_type = 'application/json'
    )
    resp_json = json.loads(resp.data.decode('utf-8'))
    access_token = resp_json['access_token']
    
    # 사용자 1의 트윗을 확인해서 트윗 리스트가 비어있는 것을 확인
    resp = api.get(f'/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))
    
    assert resp.status_code == 200
    assert tweets   == {
            'user_id' : 1,
            'timeline' : [ ]
    }
    
    # follow 사용자 아이디 = 2
    resp = api.post(
        '/follow',
        data = json.dumps({'id':1, 'follow' : 2}),
        content_type = 'application/json',
        headers = {'Authorization' : access_token}
    )
    
    assert resp.status_code == 200
    
    # 사용자 1의 트윗을 확인해서 사용자 2의 트윗이 리턴되는지 확인
    resp = api.get(f'/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))
    
    assert resp.status_code == 200
    assert tweets   == {
            'user_id' : 1,
            'timeline' : [ 
                {
                    'user_id' : 2,
                    'tweet' : "Hello World!"
                }
            ]
        }

def test_unfollow(api) :
    # 로그인
    resp = api.post(
        '/login',
        data = json.dumps({'email' : 'thunder@gmail.com', 'password' : 'test password'}),
        content_type = 'application/json'
    )
    resp_json = json.loads(resp.data.decode('utf-8'))
    access_token = resp_json['access_token']
    
    # 사용자 아이디 2
    resp = api.post(
        '/follow',
        data = json.dumps({'id': 1,'follow' : 2}),
        content_type = 'application/json',
        headers = {'Authorization' : access_token}
    )
    assert resp.status_code == 200
    
    # 사용자 1의 트윗을 확인해서 사용자 2의 트윗이 리턴되는지 확인
    resp = api.get(f'/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))
    
    assert resp.status_code == 200 
    assert tweets     == {
        'user_id' : 1,
        'timeline' : [
            {
                'user_id' : 2,
                'tweet'  : "Hello world!"
            }
        ]
    }
    
    # unfollow 사용자 아이디 = 2
    resp = api.post(
        '/unfollow',
        data = json.dumps({'id':1, 'unfollow' : 2}),
        content_type = 'application/json',
        headers = {'Authorization' : access_token}
    )
    assert resp.status_code == 200
    
    # 사용자 1의 트윗을 확인해서 유저 2의 트윗이 더이상 리턴되지 않는 것을 확인
    
    resp = api.get(f'/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))
    
    assert resp.status_code == 200 
    assert tweets == {
        'user_id' : 1,
        'timeline' : [ ]
    }


