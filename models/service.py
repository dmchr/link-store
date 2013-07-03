import config

DB = config.DB


def save_opml(user_id, opml):
    res = DB.select('users', where="id=$id", vars={'id': user_id})
    if res:
        return DB.insert(
            'user_opml',
            user_id=user_id,
            opml=opml
        )
    return False
