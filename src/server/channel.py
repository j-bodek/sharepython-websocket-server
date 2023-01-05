class WebSocketChannel(object):
    def __init__(self):
        self.clients = set()
        self.codespace_uuid = None

    def join(self, client):
        self.clients.add(client)

    def leave(self, client):
        self.clients.remove(client)


class WebSocketChannels(object):
    def __init__(self):
        self.channels = dict()

    def __add_channel(self, channel_id, channel):
        self.channels[channel_id] = channel

    def add_client(self, channel_id, client):
        if not self.channels.get(channel_id):
            channel = WebSocketChannel()
            channel.join(client)
            self.__add_channel(channel_id, channel)
        else:
            self.channels.get(channel_id).join(client)

    def remove_client(self, channel_id, client):
        if channel := self.channels.get(channel_id):
            channel.leave(client)

    def get_clients(self, channel_id):
        if channel_id in self.channels:
            return self.channels.get(channel_id).clients
        else:
            return set()
