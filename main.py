from fasthtml.common import *
import json

app, rt = fast_app()

db = database('blog.db')
class Post:
    id: int
    title: str
    content: str
    date: str
posts = db.create(Post, pk='id', transform=True)

if not posts():
    posts.insert(
        title="First Post", 
        content="This is stored in SQLite!", 
        date="2023-10-20"
    )

with open('config.json', 'r') as f:
    config = json.load(f)

def render_post(p):
    return Article(
        Header(H3(p.title)),
        P(p.content),
        Footer(Small(p.date))
    )

def home():
    post_list = [render_post(p) for p in posts()]
    
    return Titled(config["blogName"],
        H3(config["blogDescription"]),
        H2("Latest Posts"),
        *post_list
    )

@rt("/")
def get(): 
    return home()

serve()