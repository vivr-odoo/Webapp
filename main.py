import os
import redis
from werkzeug.urls import url_parse
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.utils import redirect
from jinja2 import Environment, FileSystemLoader
from werkzeug.middleware.shared_data import SharedDataMiddleware
import psycopg2
import smtplib

#created table for register user
conn = psycopg2.connect("dbname='vivr' user='postgres' host='localhost' password='postgres'")
cur = conn.cursor()
'''cur.execute(""" CREATE TABLE UserRegister(ID int, Name varchar(255), Email varchar(255), assword varchar(255));  """)
conn.commit()'''

class Shortly(object):

    def __init__(self, config):
        self.redis = redis.Redis(config['redis_host'], config['redis_port'])
        template_path = os.path.join(os.path.dirname(__file__), 'templates')
        self.jinja_env = Environment(loader=FileSystemLoader(template_path),
                                 autoescape=True)
        self.url_map = Map([
            Rule('/', endpoint='homepage'),
            Rule('/register', endpoint='register'),
            Rule('/login', endpoint='login')
        ])

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, f'on_{endpoint}')(request, **values)
        except HTTPException as e:
            return e

    def render_template(self, template_name, **context):
        t = self.jinja_env.get_template(template_name)
        return Response(t.render(context), mimetype='text/html')


    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def on_homepage(self, request):
        return self.render_template('Home/index.html')

    def on_register(self, request):
        error = None
        otp = ''
        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
            try:
                cur.execute(f""" INSERT INTO UserRegister VALUES (2,'{name}', '{email}', '{password}'); """)
                otp = 'ok'
                #conn.commit()
            except:
                error = 'Email or Password Already Exist.'
            return redirect(f"/login")
        return self.render_template('User/register.html', error=error, otp=otp)

    def on_login(self, request):
        error = None
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
        return self.render_template('User/login.html')


def create_app(redis_host='localhost', redis_port=6379, with_static=True):
    app = Shortly({
        'redis_host':       redis_host,
        'redis_port':       redis_port
    })
    if with_static:
        app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
            '/static':  os.path.join(os.path.dirname(__file__), 'static')
        })
    return app

if __name__ == '__main__':
    from werkzeug.serving import run_simple
    app = create_app()
    run_simple('127.0.0.1', 5000, app, use_debugger=True, use_reloader=True)