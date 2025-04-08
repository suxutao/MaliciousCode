from flask import Flask, request, render_template

app = Flask(__name__)

class User:
    def __init__(self,username):
        self.username=username


@app.route('/')
def hello_world():  # put application's code here
    user = User("李四")
    return render_template('index.html',user=user)


@app.route('/blog/<int:blog_id>')
def blog(blog_id):
    user=User("张三")
    return render_template('index.html',blog_id=blog_id,user=user)


@app.route('/book/')
def book():
    page = request.args.get('page', type=int, default=1)
    return f"返回第{page}页的数据"

@app.route('/filter')
def filter():
    user = User("张三xxxx")
    return render_template('filter.html',user=user)


if __name__ == '__main__':
    app.run()
