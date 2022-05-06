import tornado;
import tornado.web;
import tornado.ioloop;
import tornado.template;
import os;
import sys;
from env import *



class BaseHandler(tornado.web.RequestHandler):

    _username = adminLogin;
    _password = adminPassword;

    def isAdmin(self):
        return self.get_secure_cookie("password") == self._password and self.get_secure_cookie("user") == self._username;
    
class RootHandler(BaseHandler):
    def get(self):
        if not self.get_secure_cookie("user"):
            self.redirect("/login")
            return;
        if not self.isAdmin():
            self.clear_all_cookies();
            self.set_status(400)
            self.finish("<html><body>Error while logging in. Check your login and password</body></html>")
        self.redirect("/list");

class LoginHandler(BaseHandler):
    def get(self):
        self.write('<html><body>'
                   '<form action="/login" method="post">'
                   'Username: <input type="text" name="username">'
                   'Password: <input type="password" name="password">'
                   '<input type="submit" value="Login">'
                   '</form>'
                   '</body></html>')

    def post(self):
        self.set_secure_cookie("user", self.get_argument("username"))
        self.set_secure_cookie("password", self.get_argument("password"))
        self.redirect("/")

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_all_cookies();
        self.redirect("/");

class ListHandler(BaseHandler):
    def get(self):
        treeRes = make_results_tree(pathToServer);
        uploadMessage = "";
        if (self.isAdmin()):
            if "uploaded" in self.request.arguments:
                uploadMessage = "Successfully uploaded " + self.request.arguments["uploaded"][0].decode("utf-8");
            elif "invalidPath" in self.request.arguments:
                uploadMessage = "Provided path is invalid"
            self.render("authTree.html", tree=treeRes, uploadMessage=uploadMessage);
        else:
            self.render("tree.html", tree=treeRes);

class UploadHandler(tornado.web.RequestHandler):
    def post(self):
        inputFile = self.request.files['inputFile'][0];
        fileName = inputFile['filename']

        try:
            outputFile = open(pathToServer + self.get_argument("uploadPath") + "/" + fileName, 'wb+')
        except:
            self.redirect("/list?invalidPath=true");
            return;
        
        outputFile.write(inputFile['body'])
        outputFile.close();

        self.redirect("/list?uploaded=" + inputFile['filename']);

def make_results_tree(path):
    tree = dict(name=path[(len(pathToServer) - 1):], children=[])
    lst = os.listdir(path)
    for name in lst:
        fn = os.path.join(path, name)
        if os.path.isdir(fn):
            tree['children'].append(make_results_tree(fn))
        else:
            tree['children'].append(dict(name=name))
    return tree

if (len(sys.argv) != 3):
    print("Usage: ./server.py [port] [pathToServer]");
    exit();


application = tornado.web.Application([
    (r"/", RootHandler),
    (r"/login", LoginHandler),
    (r"/list", ListHandler),
    (r"/logout", LogoutHandler),
    (r"/upload", UploadHandler)
], cookie_secret=cookieSecret)

server = tornado.httpserver.HTTPServer(application)
server.bind(serverPort);
server.start(0)
tornado.ioloop.IOLoop.current().start()
