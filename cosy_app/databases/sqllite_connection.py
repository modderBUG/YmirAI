import sqlite3
from sqlite3 import Error
from werkzeug.security import generate_password_hash, check_password_hash

# 加密密码
def hash_password(password):
    return generate_password_hash(password)

# 验证密码
def verify_password(stored_password, provided_password):
    return check_password_hash(stored_password, provided_password)


class Database:
    def __init__(self):
        """ 初始化数据库连接 """
        db_file = "D:\projects\pythonproject\YmirAI\cosy_app\databases\chatbot.db"
        self.connection = None
        try:
            self.connection = sqlite3.connect(db_file)
            print(f"Connected to database: {db_file}")
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
        print(query,params)
        cursor.execute(query, params)

        return cursor.fetchall()

class UserService(Database):

    def insert_user(self, username, password, email):
        """ 插入新用户 """
        hashed_password = hash_password(password)  # 哈希处理密码
        query = "INSERT INTO Users (username, password, email) VALUES (?, ?, ?)"
        self.execute_query(query, (username, hashed_password, email))
        uid = self.get_uid_by_uname(username)
        self.add_credits_by_uid(uid, 80)

    def login_user(self, username, password):
        query = "SELECT password FROM Users WHERE username = ?"
        stored_password = self.fetch_all(query, (username,))
        if stored_password and verify_password(stored_password[0][0], password):
            return True
        else:
            return False

    def get_uid_by_uname(self, uname):
        try:
            query = """SELECT "uid", "username", "nickname", "password", "email", "created_at", "updated_at" FROM "Users" WHERE  "username"=?;"""
            res = self.fetch_all(query, (uname,))
            return res[0][0]
        except Exception as e:
            print(e)
            print(query)
            return None

    def get_info_by_uid(self, uid):
        query = """SELECT "uid", "username", "nickname",  "email", "created_at", "updated_at" FROM "Users" WHERE  "uid"=?;"""
        res = self.fetch_all(query, (uid,))
        return res[0]

    def add_credits_by_uid(self, uid, credit_num):
        query = """INSERT INTO "Credits" ("uid", "credits") VALUES (3, 80);"""
        self.execute_query(query, (uid, credit_num))

    def update_credits_by_uid(self, uid, credit_num):
        query = """UPDATE "Credits" SET "credits"=?  WHERE  "uid"=?;"""
        self.execute_query(query, (credit_num, uid))


class ConvService(Database):
    def insert_message(self, convid, user_text, bot_text,round_num):
        query = """INSERT INTO "ChatRecords" ("convID", "user_text", "bot_text", "ground") VALUES (?, ?, ?,?);"""
        self.execute_query(query, (convid, user_text, bot_text,round_num))

    def find_msg_by_convid(self,convid):
        sql = """SELECT * FROM "ChatRecords" WHERE  "convID"=?;"""
        res = self.fetch_all(sql,(convid,))
        return res

    def insert_conversation(self,uid,summery):
        sql = """INSERT INTO "Conversations" ("uid", "summary") VALUES (?, ?);"""
        self.execute_query(sql,(uid,summery))

    def get_all_conversation_by_uid(self,uid):
        sql = """SELECT "convID", "summary" FROM "Conversations" WHERE  "uid"=? and "del_flag"<>1;"""
        res = self.fetch_all(sql, (uid,))
        return res




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
CREATE TABLE IF NOT EXISTS ChatRecords (
    recordID INTEGER PRIMARY KEY AUTOINCREMENT,
    convID INTEGER,
    user_text TEXT,
    bot_text TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    summary TEXT,
    FOREIGN KEY (convID) REFERENCES Conversations(convID) ON DELETE CASCADE
);
"""

# 示例用法
if __name__ == "__main__":
    db = Database()

    # 创建表
    db.create_table(create_users_table)
    db.create_table(create_credits_table)
    db.create_table(create_conversations_table)
    db.create_table(create_chat_records_table)

    # db.execute_query()

    # 关闭数据库连接
    db.close()

    user_service = UserService()

    # user_service.insert_user("admin","123456","admin@qq.com")

    # a =  user_service.login_user("admin","123456")
    # print(a )

    # res = user_service.get_uid_by_uname("admin")
    # print(res)

    # user_service.update_credits_by_uid(3,"99999")

    # res = user_service.get_info_by_uid(3)
    # print(res)


    cs =ConvService()
    # cs.insert_message(1,"aaaa","vvvvv",4)
    # print(cs.find_msg_by_convid(1))
    # print(cs.get_all_conversation_by_uid(3))