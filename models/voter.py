import database, peewee


class Voter(peewee.Model):
    user_id: int = peewee.IntegerField(unique=True)
    voted: bool = peewee.BooleanField(default=False)

    class Meta:
        database = database.db
