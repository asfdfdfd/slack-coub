#!/usr/bin/python3

from tornado.gen import coroutine
from tornado.ioloop import IOLoop
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.httpserver import HTTPServer
from tornado.httputil import url_concat
from tornado.web import Application, RequestHandler

import json
import random

class CoubRandomHandler(RequestHandler):
    
    def initialize(self):
        self.timeout_expired = False
    
    def coub_url(self, query, order_by, page):
        return url_concat('https://coub.com/api/v2/search/coubs', {'q': query, 'order_by': order_by, 'page': page})

    def callback_timeout(self):
        self.timeout_expired = True

        self.write({
            'response_type': 'in_channel'
        })
        
        self.finish()
                
    @coroutine
    def get(self):                        
        query = self.get_argument('text')
        order_by = self.get_argument('order_by', 'likes_count')
        response_url = self.get_argument('response_url')

        handle_timeout = IOLoop.instance().call_at(IOLoop.instance().time() + 2, self.callback_timeout)
 
        http_client = AsyncHTTPClient()
        
        response = yield http_client.fetch(self.coub_url(query, order_by, 1))

        response_body = json.loads(response.body.decode('utf-8'))
              
        total_pages = response_body['total_pages']
        
        if total_pages > 0:
            page_number = self.random_exponential(response_body['total_pages'])
                        
            response = yield http_client.fetch(self.coub_url(query, order_by, page_number))                        
                                
            response_body = json.loads(response.body.decode('utf-8'))
            
            coub = random.choice(response_body['coubs'])

            response_body = {
                'response_type': 'in_channel',         
                'attachments':[{
                    'fallback': coub['title'],
                    'title': coub['title'],
                    'title_link': 'https://coub.com/view/%s' % coub["permalink"],
                    'image_url': coub["gif_versions"]["email"]
                }]
            }

            IOLoop.instance().remove_timeout(handle_timeout)

            if self.timeout_expired:
                response_headers = {'Content-Type': 'application/json; charset=UTF-8'}
            
                request_response = HTTPRequest(url=response_url, method='POST', headers=response_headers, body=json.dumps(response_body))

                yield http_client.fetch(request_response)
            else:
                self.write(response_body)
        else:
            response_body = {
                'text':'Could not find coub with query "%s"' % query
            }
            
            IOLoop.instance().remove_timeout(handle_timeout)

            if self.timeout_expired:                        
                response_body['response_type'] = 'in_channel'
                
                response_headers = {'Content-Type': 'application/json; charset=UTF-8'}

                request_response = HTTPRequest(url=response_url, method='POST', headers=response_headers, body=json.dumps(response_body))

                yield http_client.fetch(request_response)
            else:
                self.write(response_body)
            
    def random_exponential(self, value_max):
        return (random.expovariate(value_max / 10.0) * value_max) % value_max
                    
controllers = [
    (r'/api/v1/coub/random/?', CoubRandomHandler),
]

app = Application(controllers, debug=True)

if __name__ == '__main__':
    http_server = HTTPServer(app)
    http_server.listen(18357)

    IOLoop.instance().start()
