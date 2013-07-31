import config

DB = config.DB


def login(username):
    res = DB.select('users', where="name=$name", vars={'name': username})
    if res:
        return res[0]
    return False


def get_users():
    return DB.select('users')
