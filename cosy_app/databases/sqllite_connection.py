import json
import sqlite3
import traceback
from sqlite3 import Error
from werkzeug.security import generate_password_hash, check_password_hash
import os
import base64
# from configs.config_prompts import prompts_kesya,prompts_yixian
import pymysql
from databases.config_database import mysql_config
from datetime import datetime

# 加密密码
def hash_password(password):
    return generate_password_hash(password)


# 验证密码
def verify_password(stored_password, provided_password):
    return check_password_hash(stored_password, provided_password)


class Database:
    def __init__(self):
        """ 初始化数据库连接 """
        # db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chatbot.db')
        # print(db_file)
        # db_file = "D:\projects\pythonproject\YmirAI\cosy_app\databases\chatbot.db"
        self.connection = None
        try:
            self.connection =  pymysql.connect(**mysql_config)   #  sqlite3.connect(db_file)
            print(f"Connected to database: {mysql_config.get('host')}")
        except Error as e:
            print(f"Error connecting to database: {e}")

    def close(self):
        """ 关闭数据库连接 """
        if self.connection:
            self.connection.close()
            print("Database connection closed.")

    def create_table(self, create_table_sql):
        """ 创建表 """
        try:
            cursor = self.connection.cursor()
            cursor.execute(create_table_sql)
            print("Table created successfully.")
        except Error as e:
            print(f"Error creating table: {e}")

    def execute_query(self, query, params=()):
        """ 执行单个查询 """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            print("Query executed successfully.")
            return cursor.lastrowid
        except Error as e:
            print(f"Error executing query: {e}")

    def fetch_all(self, query, params=()):
        """ 获取所有结果 """
        cursor = self.connection.cursor()
        print(query, params)
        cursor.execute(query, params)

        return cursor.fetchall()


class UserService(Database):

    def insert_user(self, username, password, email):
        """ 插入新用户 """
        hashed_password = hash_password(password)  # 哈希处理密码
        query = "INSERT INTO Users (username, password, email) VALUES (%s, %s, %s)"
        self.execute_query(query, (username, hashed_password, email))
        uid = self.get_uid_by_uname(username)
        self.add_credits_by_uid(uid, 80)

    def login_user(self, username, password):
        query = "SELECT password FROM Users WHERE username = %s"
        stored_password = self.fetch_all(query, (username,))
        if stored_password and verify_password(stored_password[0][0], password):
            return True
        else:
            return False

    def get_uid_by_uname(self, uname):
        query = """ 
                SELECT `uid`, `username`, `nickname`, `password`, `email`, `created_at`, `updated_at` 
                FROM `Users` 
                WHERE  `username`=%s;
                """
        try:
            res = self.fetch_all(query, (uname,))
            return res[0][0]
        except Exception as e:
            print(traceback.format_exc())
            print(f"error : {str(e)}\n{query}")
            return None

    def get_uid_by_email(self, email):
        query = """SELECT uid FROM Users WHERE  email=%s;"""
        try:
            res = self.fetch_all(query, (email,))
            return res[0][0]
        except Exception as e:
            print(e)
            print(query)
            return None

    def get_info_by_uid(self, uid):
        query = """SELECT uid, username, nickname,  email, created_at, updated_at FROM Users WHERE  uid=%s;"""
        res = self.fetch_all(query, (uid,))
        format_res = []
        for line in res[0]:
            _line = [i.strftime('%Y-%m-%d %H:%M:%S') if isinstance(i, datetime) else i for i in line]
            format_res.append(_line)

        return format_res

    def add_credits_by_uid(self, uid, credit_num):
        query = """INSERT INTO Credits (uid, credits) VALUES (3, 80);"""
        self.execute_query(query, (uid, credit_num))

    def update_credits_by_uid(self, uid, credit_num):
        query = """UPDATE Credits SET credits=%s  WHERE  uid=%s;"""
        self.execute_query(query, (credit_num, uid))


class ConvService(Database):
    def insert_message(self, convid, user_text, bot_text, round_num):
        query = """INSERT INTO ChatRecords (convID, user_text, bot_text, ground) VALUES (%s, %s, %s, %s);"""
        self.execute_query(query, (convid, user_text, bot_text, round_num))

    def find_msg_by_convid(self, convid):
        sql = """SELECT * FROM  ChatRecords  WHERE   convID =%s;"""
        res = self.fetch_all(sql, (convid,))
        return res

    def insert_conversation(self, uid, summery):
        sql = """INSERT INTO  Conversations  ( uid ,  summary ) VALUES (%s, %s);"""
        self.execute_query(sql, (uid, summery))

    def get_all_conversation_by_uid(self, uid):
        sql = """SELECT  convID ,  summary  FROM  Conversations  WHERE   uid=%s and del_flag<>1;"""
        res = self.fetch_all(sql, (uid,))
        return res

    def update_summary_by_convid(self, summary, convid, uid):
        sql = """UPDATE `Conversations` SET `summary`=%s WHERE  `convID`=%s and `uid`=%s;"""
        res = self.execute_query(sql, (summary, convid, uid))
        return res

    def update_conv_by_convid(self, conv_text, convid, uid,character_id):
        sql = """ 
        UPDATE `Conversations` 
        SET `conv`=%s ,`character_id`=%s
        WHERE  `convID`=%s and `uid`=%s;"""
        res = self.execute_query(sql, (conv_text, character_id,convid, uid))
        return res

    def get_conv_by_convid(self, convid, uid):
        sql = """ SELECT `convID`, `conv` FROM `Conversations` WHERE  `convID`=%s and `uid`=%s;"""
        res = self.fetch_all(sql, (convid, uid))
        return res

    def generate_convid(self, uid, summary):
        try:
            sql = """ INSERT INTO `Conversations` (`uid`, `summary`) VALUES (%s, %s);"""
            cursor = self.connection.cursor()
            cursor.execute(sql, (uid, summary))
            self.connection.commit()
            print("Query executed successfully.")
            return cursor.lastrowid  # 返回插入的行 ID
        except Error as e:
            print(f"Error executing query: {e}")
            return None  # 在发生错误时返回 None


class AudioService(Database):
    def insert_audio(self, uid, filename, mime_type, prompts_text, text, audio_data):
        query = """ INSERT INTO `audio_files` (`uid`, `file_name`, `mime_type`, `prompts_text`, `text`, `audio_data`)  VALUES (%s, %s, %s,%s,%s,%s); """
        self.execute_query(query, (uid, filename, mime_type, prompts_text, text, audio_data))

    def delete_audio(self, id):
        # query = """DELETE FROM "audio_files" WHERE  "id"=%s;"""
        query = """ UPDATE `audio_files` SET `del_flag`=1 WHERE  `id`=%s; """
        self.execute_query(query, (id,))

    def get_all_by_uid(self, uid):
        sql = """
        SELECT `id`, `uid`, `file_name`, `mime_type`, `prompts_text`, `text`, `upload_date`, `audio_data` 
        FROM `audio_files` 
        WHERE  `uid`=%s AND `del_flag`<>1;
        """
        res = self.fetch_all(sql, (uid,))

        res = [{
            "id": item[0],
            "uid": item[1],
            "file_name": item[2],
            "mime_type": item[3],
            "prompts_text": item[4],
            "text": item[5],
            "upload_date": item[6].strftime('%Y-%m-%d %H:%M:%S'),
        } for item in res]
        return res

    """
            format_res = []
        for line in res[0]:
            _line = [i.strftime('%Y-%m-%d %H:%M:%S') if isinstance(i, datetime) else i for i in line]
            format_res.append(_line)
            
            """

    def get_b64data_by_id(self, id):
        sql = """ SELECT  `audio_data` FROM `audio_files` WHERE  `id`=%s and `del_flag`<>1; """
        res = self.fetch_all(sql, (id,))
        audio_base64 = base64.b64encode(res[0][0]).decode('utf-8')
        return audio_base64


class CharacterService(Database):
    def insert_character(self, uid, character_name, summery, prompts_texts, text, audio_data, avatar, publish):
        query = """ 
        INSERT INTO `characters` 
        (`uid`, `character_name`, `summery`, `prompts_texts`, `text`, `audio_data`, `avatar`, `publish`, `del_flag`) 
        VALUES (%s, %s, %s, %s, %s, %s, %s,%s, 0);
        """
        self.execute_query(query, (uid, character_name, summery, prompts_texts, text, audio_data, avatar, publish))

    def delete_character(self, id, uid):
        # query = """DELETE FROM "audio_files" WHERE  "id"=%s;"""
        query = """ UPDATE `characters` SET `del_flag`=1 WHERE  `id`=%s AND `uid`=%s; """
        self.execute_query(query, (id, uid))

    def publish_character(self, id, uid):
        # query = """DELETE FROM "audio_files" WHERE  "id"=%s;"""
        query = """UPDATE `characters` SET `publish`=1 WHERE  `id`=%s AND `uid`=%s; """
        self.execute_query(query, (id, uid))


    def get_prompts_by_id(self, id):
        sql = """
        SELECT `prompts_texts`
        FROM `characters`
        WHERE  id =%s 
        """
        res = self.fetch_all(sql, (id,))
        return res[0][0]


    def get_text_by_id(self, id):
        sql = """
        SELECT `text`
        FROM `characters`
        WHERE  id =%s 
        """
        res = self.fetch_all(sql, (id,))
        return res[0][0]

    def get_all_characters_by_uid(self, uid):
        sql = """
        SELECT `id`, `uid`, `character_name`, `summery`, `prompts_texts`, `text`, `upload_date`,  `avatar`, `publish` 
        FROM `characters`
        WHERE  `uid`=%s AND `del_flag`<>1 limit 5;
        """
        res = self.fetch_all(sql, (uid,))

        res = [{
            "id": item[0],
            "uid": item[1],
            "character_name": item[2],
            "summery": item[3],
            "prompts_texts": json.loads(item[4]),
            "text": item[5],
            "upload_date": item[6].strftime('%Y-%m-%d %H:%M:%S'),
            "avatar": item[7],
            "publish": item[8],
        } for item in res]
        return res

    def get_all_characters_info_by_uid(self, uid):
        sql = """
        SELECT `id`, `uid`, `character_name`, `summery`, `prompts_texts`, `text`, `upload_date`,  `publish` 
        FROM `characters`
        WHERE  `uid`=%s AND `del_flag`<>1 limit 20;
        """
        res = self.fetch_all(sql, (uid,))

        res = [{
            "id": item[0],
            "uid": item[1],
            "character_name": item[2],
            "summery": item[3],
            "prompts_texts": json.loads(item[4]),
            "text": item[5],
            "upload_date": item[6].strftime('%Y-%m-%d %H:%M:%S'),
            "publish": item[7],
        } for item in res]
        return res

    def get_published_characters_info(self,limit,offset):
        sql = """
        SELECT `id`, `uid`, `character_name`, `summery`, `prompts_texts`, `text`, `upload_date`,  `publish` 
        FROM `characters`
        WHERE  `publish`=1 AND `del_flag`<>1 limit %s OFFSET %s;
        """
        res = self.fetch_all(sql,(limit,offset))

        res = [{
            "id": item[0],
            "uid": item[1],
            "character_name": item[2],
            "summery": item[3],
            "prompts_texts": json.loads(item[4]),
            "text": item[5],
            "upload_date": item[6].strftime('%Y-%m-%d %H:%M:%S'),
            "publish": item[7],
        } for item in res]
        return res

    def get_character_b64data_by_id(self, id):
        sql = """ SELECT  `audio_data` FROM `characters` WHERE  `id`=%s and `del_flag`<>1;"""
        res = self.fetch_all(sql, (id,))
        audio_base64 = base64.b64encode(res[0][0]).decode('utf-8')
        return audio_base64
    def get_character_avatar_by_id(self, id):
        sql = """ SELECT  `avatar` FROM `characters` WHERE  `id`=%s and `del_flag`<>1; """
        res = self.fetch_all(sql, (id,))
        audio_base64 = base64.b64encode(res[0][0]).decode('utf-8')
        return audio_base64
    def get_character_audio_by_id(self, id):
        sql = """ SELECT  `audio_data` FROM `characters` WHERE  `id`=%s and `del_flag`<>1; """
        res = self.fetch_all(sql, (id,))
        return res[0][0]


# SQL 表创建语句
create_users_table = """
CREATE TABLE IF NOT EXISTS Users (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    nickname TEXT,
    password TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

create_credits_table = """
CREATE TABLE IF NOT EXISTS Credits (
    uid INTEGER,
    credits INTEGER DEFAULT 0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uid) REFERENCES Users(uid) ON DELETE CASCADE
);
"""

create_conversations_table = """
CREATE TABLE IF NOT EXISTS Conversations (
    convID INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER,
    summary TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uid) REFERENCES Users(uid) ON DELETE CASCADE
);
"""

create_chat_records_table = """
CREATE TABLE "ChatRecords" (
	"recordID" INTEGER NOT NULL,
	"convID" INTEGER NULL,
	"user_idx" TINYINT NOT NULL,
	"user_texts" TEXT NULL,
	"bot_texts" TEXT NULL,
	"bot_idx" INTEGER NOT NULL,
	"suitable" TEXT NULL,
	"voice" TEXT NULL,
	"timestamp" DATETIME NULL,
	PRIMARY KEY ("recordID"),
	CONSTRAINT "0" FOREIGN KEY ("convID") REFERENCES "Conversations" ("convID") ON UPDATE NO ACTION ON DELETE CASCADE
)
;
"""

create_audio_files_table = """
CREATE TABLE audio_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    prompts_text TEXT NOT NULL,
    text TEXT NOT NULL,
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    audio_data BLOB NOT NULL,
    del_flag TINYINT NOT NULL,
    CONSTRAINT "0" FOREIGN KEY ("uid") REFERENCES "Users" ("uid") ON UPDATE NO ACTION ON DELETE CASCADE
);

"""

create_characters_table = """
CREATE TABLE characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    character_name TEXT NOT NULL,
    summery TEXT NOT NULL,
    prompts_texts TEXT NOT NULL,
    text TEXT NOT NULL,
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    audio_data BLOB NOT NULL,
    avatar BLOB NOT NULL,
    publish TINYINT NOT NULL,
    del_flag TINYINT NOT NULL,
    CONSTRAINT "0" FOREIGN KEY ("uid") REFERENCES "Users" ("uid") ON UPDATE NO ACTION ON DELETE CASCADE
);
"""



def _test_insert_character():
    ccss = CharacterService()
    # file2 = open(r"D:\projects\pythonproject\YmirAI\assert\85px-yixian.jpg","rb")
    # file = open(r"D:\projects\pythonproject\YmirAI\cosy_app\character\yixian\rwertoem4id64mao2x9hcs96l4tstnu.mp3","rb")
    # prompt_text = "嗯，对女性做出这样的举动，想必指挥官也做好承担后果的心理准备了吧？"
    # prompts_text = [
    #     {"role": "system", "content": f"{prompts_yixian}"},
    #     {"role": "assistant", "content": f"想我了么？指挥官大人。"},
    # ]

    file2 = open(r"D:/projects/YmirAI-web/src/assets/imgs/kesya.jpg", "rb")
    file = open(r"D:\projects\pythonproject\YmirAI\cosy_app\character\kesya\加班后要去喝一杯吗？嗯？你不会忍心，让我一个人去吧。...我不想在这停留太久。...要找我的话，你有我的号码。.mp3", "rb")
    prompt_text = "加班后要去喝一杯吗？嗯？你不会忍心，让我一个人去吧。...我不想在这停留太久。...要找我的话，你有我的号码。"
    prompts_text = [
        {"role": "system", "content": f"{prompts_kesya}"},
        {"role": "assistant", "content": f"想我了么？呵呵。"},
    ]

    ccss.insert_character(3,"凯茜娅-模板","凯茜娅的内置模板",prompts_texts=json.dumps(prompts_text),text=prompt_text,audio_data=file.read(),avatar=file2.read(),publish=1)
    ccss.close()


"""
[
    {
        "speaker": "human",
        "speech": "你好"
    },
    {
        "idx": 0,
        "loading": false,
        "speaker": "ai",
        "suitable": [
            0
        ],
        "speeches": [
            "嗨，阿顺，有什么新的任务或者挑战吗？或者只是想聊聊天？不管怎样，我都在这里，准备好为你提供帮助或陪伴了。"
        ]
    },
    {
        "speaker": "human",
        "speech": "你好啊哈哈哈"
    },
    {
        "idx": 0,
        "loading": false,
        "speaker": "ai",
        "suitable": [
            0
        ],
        "speeches": [
            "哈哈，你好，阿顺！有时候我也会觉得生活中的小乐趣比任何任务都来得重要。所以，不论是工作还是轻松一刻，都欢迎来找我聊聊。"
        ]
    }
]

"""
# 示例用法
if __name__ == "__main__":
    db = Database()

    # 创建表
    # db.create_table(create_users_table)
    # db.create_table(create_credits_table)
    # db.create_table(create_conversations_table)
    # db.create_table(create_chat_records_table)

    # db.execute_query()

    # 关闭数据库连接
    db.close()

    user_service = UserService()

    # user_service.insert_user("admin","123456","admin@qq.com")

    a =  user_service.login_user("admin","123456")
    print(a )

    # res = user_service.get_uid_by_uname("admin")
    # print(res)

    # user_service.update_credits_by_uid(3,"99999")

    # res = user_service.get_info_by_uid(3)
    # print(res)

    cs = ConvService()
    # cs.insert_message(1,"aaaa","vvvvv",4)
    # print(cs.find_msg_by_convid(1))
    # print(cs.get_all_conversation_by_uid(3))

    print(cs.generate_convid(3,""))
    # print(cs.update_summary_by_convid("bbb",4,3))

    # print(cs.get_conv_by_convid(4,3))

    ass = AudioService()

    # with open(r'D:\projects\pythonproject\YmirAI\cosy_app\character\zhenhai\qdv4aga7uz1nrx48otvpf04ivrn0hvy.mp3',"rb") as f:
    #     data = f.read()
    # ass.insert_audio("3","逸仙","wav","你是在思考吗？还是说，只是单纯的在发呆？表情倒是挺可爱的呢，呵呵...","你好，分析员。[breath]想我了吗[laughter]",data)

    # print(ass.get_all_by_uid(3))
    # print(ass.get_data_by_id(1))

    ccss = CharacterService()

    print(ccss.get_all_characters_info_by_uid(3))

    # print(ccss.get_all_characters_info_by_uid(3))
    #
    # file2 = open(r"D:\projects\pythonproject\YmirAI\assert\85px-yixian.jpg","rb")
    # file = open(r"D:\projects\pythonproject\YmirAI\cosy_app\character\yixian\rwertoem4id64mao2x9hcs96l4tstnu.mp3","rb")
    # prompt_text = "嗯，对女性做出这样的举动，想必指挥官也做好承担后果的心理准备了吧？"
    # prompts_text = [
    #     {"role": "system", "content": f"{prompts_kesya}"},
    #     {"role": "assistant", "content": f"想我了么？"},
    # ]
    # ccss.insert_character(3,"逸仙-test","测试一线",prompts_texts=json.dumps(prompts_text),text=prompt_text,audio_data=file.read(),avatar=file2.read(),publish=0)

    # _test_insert_character()
