def test_main_succeeds():
    assert True


def test_hello():
    from telegram_to_rss import main

    assert main.get_hello() == "hello"
