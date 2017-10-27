import json
import asyncio

from aiohttp.web import Response, StreamResponse
from aiohttp.web import HTTPMethodNotAllowed

from aiohttp_traversal.abc import AbstractView


class View(AbstractView):
    def __init__(self, request, resource, tail):
        self.request = request
        self.resource = resource
        self.tail = tail

    @asyncio.coroutine
    def __call__(self):
        raise NotImplementedError()


class WebsocketView(View):
    """ React type of websocket view
        Should we support binary type message ?
    """

    @asyncio.coroutine
    def on_open(self):
        """ Callback right after prepare websocket response 
        """
        pass

    @asyncio.coroutine
    def on_close(self):
        """ Callback before terminate object 
        """
        pass

    @asyncio.coroutine
    def on_message(self, message):
        """ Callback when receive a message
        """
        pass

    @asyncio.coroutine
    def __call__(self):

        #Prepare the response
        self.ws = WebSocketResponse()
        ok, protocol = self.ws.can_prepare(request)
        if not ok:
            return Response(
                body="%s was meant to be called through ws protocol " % url, 
                content_type='text/plain')

        yield from self.ws.prepare(request)

        yield from self.on_open()

        async for msg in self.ws:
            if msg.type == WSMsgType.TEXT:
                #Normal data ?
                yield from self.on_message(msg.data)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                #Exception
                print('ws connection closed with exception %s' %
                    self.ws.exception())
                break

        yield from self.on_close()

        return self.ws



class MethodsView(View):
    methods = frozenset(('get', 'post', 'put', 'patch', 'delete', 'option'))  # {'get', 'post', 'put', 'patch', 'delete', 'option'}

    @asyncio.coroutine
    def __call__(self):
        method = self.request.method.lower()

        if method in self.methods:
            return (yield from getattr(self, method)())
        else:
            raise HTTPMethodNotAllowed(method, self.methods)

    @asyncio.coroutine
    def get(self):
        raise NotImplementedError()

    @asyncio.coroutine
    def post(self):
        raise NotImplementedError()

    @asyncio.coroutine
    def put(self):
        raise NotImplementedError()

    @asyncio.coroutine
    def patch(self):
        raise NotImplementedError()

    @asyncio.coroutine
    def delete(self):
        raise NotImplementedError()

    @asyncio.coroutine
    def option(self):
        raise NotImplementedError()


class RESTView(MethodsView):
    def serialize(self, data):
        """ Serialize data to JSON.

        You can owerride this method if you data cant be serialized
        standart json.dumps routine.
        """
        return json.dumps(data).encode('utf8')

    @asyncio.coroutine
    def __call__(self):
        data = yield from super().__call__()

        if isinstance(data, StreamResponse):
            return data
        else:
            return Response(
                body=self.serialize(data),
                headers={'Content-Type': 'application/json; charset=utf-8'},
            )
