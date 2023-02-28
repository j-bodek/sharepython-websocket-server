WebSocket server used by [**PythonShare**](https://github.com/LilJack118/sharepython "**PythonShare**"). Build with scalability and high performence in mind. It defines only one endpoint responsible for handling codespace updates.

#### Tech Stack:
- [**Sanic**](https://github.com/sanic-org/sanic "**Sanic**") - fast and light weighted python framework that allow to handle websocket connections. It uses ASGI interface to allow building async servers.
- [**aioredis**](https://github.com/aio-libs/aioredis-py "**aioredis**") - async interface to redis
- [**haproxy**](http://www.haproxy.org/ "**haproxy**") - loadbalancer. As i said one of my goal was to write solution that can scale. Scaling websocket server vertically isn't best idea so i decided to scale it horizontally. And loadbalancer is used to distribute incomming connections between websocket server instances. [**HERE**](https://github.com/LilJack118/sharepython/blob/main/docker-compose.yml "**here**") you can take a look on basic setup of haproxy with docker-compose to distribute incoming connections between two websocket servers

#### How it works?
- **INCOMING CONNECTIONS**
	- When new connection is made at first it has to be authenticated. To do that i send async request to [**sharepython-api** ](https://github.com/LilJack118/sharepython-api "**sharepython-api** ")and if everything is fine it resonses with status code 200 and codespace uuid. In other case 401 and then websocket connection is closed
	- When connection is authenticated i check if Channel instance exists in ChannelsCache. If not,  new Channel instance and new PubSub instance is created.
	- After that if Channel was created i'm adding new background task responsible for listening incoming messages from PubSub channel
	- Then new client is registered (added) to Channel

- **WEBSOCKET MESSAGE**
	- when new websocket message is received it is validated and then proceeded by method corresponding method. 
	- if message is valid it is then published to corresponding pubsub channel
	- when new message is received from pubsub channel (Channel instance is responsible for that) it is send to all connected clients

#### Why I used Sanic?
Main functionality of  [**SharePython**](https://github.com/LilJack118/sharepython "**SharePython**") is ability to share code with others in real time. And it also was potentially the most heavily loaded part of application and potential bottleneck. So my main goal was to come up with solution that would ensure low latency and scalability. Since Sanic is asnyc webframework, it's quite lightweight, well maintained, and it main focus was speed and scalability, so it looked like a perfect choice (before switching to Sanic i wrote basics of this server with [websockets](https://websockets.readthedocs.io/en/stable/ "websockets") library and i have to say Sanic really sped it up).

#### Why update code in Redis and not directly in Postgres?
Answer is simple. Speed. I used redis as cache for currently used codespaces to store their code while users work with them. Since redis stores data in memory, access to it is way (i mean wayyy) faster then making query to relational database like Postgres. But very important aspact was deleting data from redis when not used for a while (setting expire value) to keep RAM usage low.

#### Whats the point of using [Redis PUB/SUB channels](https://redis.io/docs/manual/pubsub/ "Redis PUB/SUB channels")?
There is no point of using them if you are sure that you will use only one instance of websocket server. BUT when you use more then one websocket server instance, message broaker is inevitable. Let me explain. First let's briefly explain how websockets work. Since websocket is stateful protocol server must maintain the connection to keep it alive. That's why websocket connection (not request) is way more expensive then http. With only one server you can fast reach computing limit. So what then. Well first option is vertical scaling (simply get more ram and/or cpu), which is okay for small project but because there are phisicall limits to how much ram and cpu that single server can have this solution can not be enough when you will have to handle more connections. Second solution is horizontal scaling. You simply create another instance of server and distribute incoming connections to each of them using haproxy (in my case) or other loadbalancer. And now we need message broaker. It is possible for clients from the same codespace to connect to different server instances. And because you have to keep connections alive it is not possible to share them between servers. So every new websocket message is processed and published via redis pub/sub channels. Then, each Channel instance (an object representing a single codespace) listens for new messages from that channel and broadcasts them to all connected clients.