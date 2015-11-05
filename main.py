#!/usr/bin/python3

from tornado.gen import coroutine
from tornado.ioloop import IOLoop
from tornado.httpclient import AsyncHTTPClient
from tornado.httpserver import HTTPServer
from tornado.httputil import url_concat
from tornado.web import Application, RequestHandler

import json
import random

class CoubRandomHandler(RequestHandler):
    
    def coub_url(self, query, order_by, page):
        return url_concat('https://coub.com/api/v2/search/coubs', {'q': query, 'order_by': order_by, 'page': page})
            
    @coroutine
    def get(self):                        
        query = self.get_argument('text')
        order_by = self.get_argument('order_by', 'oldest')
        
        http_client = AsyncHTTPClient()
        
        response = yield http_client.fetch(self.coub_url(query, order_by, 1))

        response_body = json.loads(response.body.decode('utf-8'))
              
        total_pages = response_body['total_pages']
        
        if total_pages > 0:
            page_number = random.randint(1, response_body['total_pages'])
                        
            response = yield http_client.fetch(self.coub_url(query, order_by, page_number))                        
                                
            response_body = json.loads(response.body.decode('utf-8'))
            
            coub = random.choice(response_body['coubs'])

            self.write({
                'response_type': 'in_channel',         
                'attachments':[{
                    'fallback': coub['title'],
                    'title': coub['title'],
                    'title_link': 'https://coub.com/view/%s' % coub["permalink"],
                    'image_url': coub["gif_versions"]["email"]
                }]
            })
        else:
            self.write('Could not find coub.')
        
controllers = [
    (r'/api/v1/coub/random/?', CoubRandomHandler),
]

app = Application(controllers, debug=True)

if __name__ == '__main__':
    http_server = HTTPServer(app)
    http_server.listen(18357)

    IOLoop.instance().start()
