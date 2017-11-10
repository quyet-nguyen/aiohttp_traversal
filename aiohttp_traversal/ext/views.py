import json
import asyncio

from aiohttp import WSMsgType
from aiohttp.web import Response, StreamResponse, WebSocketResponse
from aiohttp.web import HTTPMethodNotAllowed

from aiohttp_traversal.abc import AbstractView


class View(AbstractView):
    def __init__(self, request, resource, tail):
        self.request = request
        self.resource = resource
        self.tail = tail

    async def __call__(self):
        raise NotImplementedError()


class WebsocketView(View):
    """ React type of websocket view
        Should we support binary type message ?
    """

    async def on_open(self):
        """ Callback right after prepare websocket response 
        """
        pass

    async def on_close(self):
        """ Callback before terminate object 
        """
        pass

    async def on_message(self, message):
        """ Callback when receive a message
        """
        pass

    async def send(self,message):
        """ Send message back to client
        """
        await self.ws.send_str(message)

    async def __call__(self):

        #Prepare the response
        self.ws = WebSocketResponse()
        ok, protocol = self.ws.can_prepare(self.request)
        if not ok:
            return Response(
                body="%s was meant to be called through ws protocol " % self.request.url, 
                content_type='text/plain')

        await self.ws.prepare(self.request)

        await self.on_open()

        try:
            async for msg in self.ws:
                if msg.type == WSMsgType.TEXT:
                    #Normal data ?
                    await self.on_message(msg.data)
                elif msg.type == WSMsgType.ERROR:
                    #Exception
                    print('ws connection closed with exception %s' %
                        self.ws.exception())
                    break
        finally:
            await self.on_close()

        return self.ws



class MethodsView(View):
    methods = frozenset(('get', 'post', 'put', 'patch', 'delete', 'option'))  # {'get', 'post', 'put', 'patch', 'delete', 'option'}

    async def __call__(self):
        method = self.request.method.lower()

        if method in self.methods:
            return (await getattr(self, method)())
        else:
            raise HTTPMethodNotAllowed(method, self.methods)

    async def get(self):
        raise NotImplementedError()

    async def post(self):
        raise NotImplementedError()

    async def put(self):
        raise NotImplementedError()

    async def patch(self):
        raise NotImplementedError()

    async def delete(self):
        raise NotImplementedError()

    async def option(self):
        raise NotImplementedError()


class RESTView(MethodsView):
    def serialize(self, data):
        """ Serialize data to JSON.

        You can owerride this method if you data cant be serialized
        standart json.dumps routine.
        """
        return json.dumps(data).encode('utf8')

    async def __call__(self):
        data = await super().__call__()

        if isinstance(data, StreamResponse):
            return data
        else:
            return Response(
                body=self.serialize(data),
                headers={'Content-Type': 'application/json; charset=utf-8'},
            )
