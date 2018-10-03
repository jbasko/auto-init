from auto_init import AutoInitContext


def test_any_default_value_is_overridden_if_there_is_explicit_provider():
    class Connection:
        pass

    class Db:
        username: str = 'root'
        connection: Connection = None

    with AutoInitContext(providers={Db: Db, Connection: Connection}) as context:
        db = context.auto_init(Db)
        assert isinstance(db, Db)
        assert isinstance(db.connection, Connection)
        assert db.username == 'root'

    # Ridiculous, but makes sense. If you specify a str provider then all strings will be set.
    with AutoInitContext(providers={Db: Db, str: ''}) as context:
        db = context.auto_init(Db)
        assert db.username == ''
        assert db.connection is None
