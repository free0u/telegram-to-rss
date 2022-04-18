from jinja2 import Environment, PackageLoader, select_autoescape

env = Environment(
    loader=PackageLoader("telegram_to_rss"), autoescape=select_autoescape()
)
