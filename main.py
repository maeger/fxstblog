from fasthtml.common import *
import json
from datetime import datetime

app, rt = fast_app()

db = database('blog.db')
class Post:
    id: int
    title: str
    content: str
    date: str
posts = db.create(Post, pk='id', transform=True)

now = datetime.now()
formatted_date = now.strftime("%Y-%m-%d")

# Create demo post if database is completely empty
if not posts():
    posts.insert(
        title="First Post", 
        content="This is your first FSXT Blog post!", 
        date=formatted_date
    )

# testing
# string = "A" * 1000000
# posts.insert(
#     title="Test post", 
#     content=string, 
#     date=formatted_date
# )

with open('config.json', 'r') as f:
    config = json.load(f)

def render_post(p, is_admin = False):
    char_limit = 500
    display_content = p.content

    delete_btn = ""
    if is_admin:
        delete_btn = Button("Delete", 
                            hx_delete=f"/posts/{p.id}", 
                            hx_confirm="Are you sure?", 
                            target_id=f"post-{p.id}", 
                            hx_swap="delete",
                            cls="outline contrast",
                            style="padding: 0.2rem 0.5rem; font-size: 0.8rem;")

    if len(display_content) > char_limit:
        display_content = display_content[:char_limit] + "..."

    return Article(
        Header(
            Grid(
                H3(A(p.title, href=f"/post/{p.id}")),
                Div(delete_btn, style="text-align: right")
            )
        ),
        # Display the truncated content
        P(display_content),
        # Add a specific "Read More" link
        Footer(
            Div(
                Small(p.date),
                A("Read full post →", href=f"/post/{p.id}", style="float: right"),
                style="display: flex; justify-content: space-between; align-items: center;"
            )
        )
    )

@rt("/post/{id}")
def get(id: int):
    # Fetch the specific post by its ID
    # In Fastlite, table[id] retrieves the record with that primary key
    try:
        p = posts[id]
    except NotFoundError:
        return Titled("404", P("Post not found!"))

    return Titled(config["blogName"],
            Titled(p.title,
            Article(
                P(p.content),
                Footer(Small(f"Published on: {p.date}"))
            ),
            # Placeholder for Comments Section
            Section(
                H4("Comments"),
                Ul(
                    Li(I("No comments yet. Be the first!")),
                    id="comment-list"
                ),
                # A simple placeholder form for adding comments
                Form(
                    Group(
                        Input(placeholder="Add a comment...", name="comment"),
                        Button("Post")
                    )
                )
            ),
            P(A("← Back to home", href="/"))
    ))

def home(session):
    is_admin = session.get('admin')
    
    # We can conditionally add a "New Post" button
    admin_tools = A("Create New Post", href="/new", cls="button") if is_admin else ""
    login_btn = A("Logout", href="/logout") if is_admin else A("Login", href="/login")

    post_list = [render_post(p, is_admin) for p in posts(order_by='id desc')]
    
    return Titled(
        A(config["blogName"], href="/"), # This makes the title a link to root
        H3(config["blogDescription"]),
        P(admin_tools),
        P(login_btn),
        H2("Latest Posts"),
        Div(*post_list, style="max-width: 75%; margin-left: 0;"),
        P("Powered by FsxtBlog")
    )

def login_form():
    return Titled("Admin Login",
        # The form sends data to the '/login' POST route
        Form(
            # 'Group' puts the label and input together nicely in Pico CSS
            Group(
                Input(type="password", name="pwd", id="pwd", placeholder="Enter admin password"),
            ),
            Button("Login", cls="primary"),
            action="/login", method="post"
        )
    )

@rt("/login")
def post(pwd: str, session):
    if pwd == "admin123":
        session['admin'] = True
        # Redirect to the home page (or an admin dashboard)
        return RedirectResponse("/", status_code=303)
    else:
        return Titled("Login Failed", 
            P("Incorrect password.", style="color: red"),
            login_form()
        )
    
@rt("/new")
def get(session):
    # Check if user is admin
    if not session.get('admin'):
        return RedirectResponse("/login", status_code=303)
    
    return Titled("Create New Post",
        Form(
            # Input names must match your database column names (title, content)
            Group(Input(name="title", placeholder="Post Title")),
            Group(Textarea(name="content", placeholder="Write your post here...", rows=10)),
            # Using Today's date automatically
            Input(type="hidden", name="date", value=datetime.now().strftime("%Y-%m-%d")),
            
            Button("Publish Post", cls="primary"),
            
            action="/new", method="post"
        ),
    )

@rt("/new")
def post(post: Post, session):
    # Security check again for the POST request
    if not session.get('admin'):
        return RedirectResponse("/login", status_code=303)
    
    # Fastlite makes saving easy: just pass the object to insert()
    posts.insert(post)
    
    # Redirect back to home to see the new post at the top
    return RedirectResponse("/", status_code=303)

@rt("/posts/{id}")
def delete(id: int, session):
    # Security check
    if not session.get('admin'): 
        return Response("Unauthorized", status_code=401)
    
    # Delete from SQLite
    posts.delete(id)
    
    # Return nothing; HTMX will remove the element with target_id
    return ""
    
@rt("/logout")
def get(session):
    session.pop('admin', None)
    return RedirectResponse("/", status_code=303)

@rt("/")
def get(session): 
    return home(session)

@rt("/login")
def get():
    return login_form()

serve()