import uuid
from typing import Callable, Dict, List

from fastapi import FastAPI
from pydantic import BaseModel
from python_aternos import AternosServer, Client


class User(BaseModel):
    username: str
    password: str
    id: uuid.UUID = None
    aternos: Client = None

    class Config:
        arbitrary_types_allowed = True

    def json(self):
        return {
            "username": self.username,
            "password": self.password,
            "id": self.id,
        }


loggedInUsers: Dict[uuid.UUID, User] = {}


class Server(BaseModel):
    userId: uuid.UUID
    serverId: str

class ServerInfo(BaseModel):
    servid: str
    address: str 


app = FastAPI()


@app.post("/login")
def login(user: User):
    username = user.username
    password = user.password
    aternos = Client.from_credentials(username, password)
    id = uuid.uuid4()
    user = User(username=username, password=password, id=id, aternos=aternos)
    loggedInUsers[user.id] = user
    return {
        "status": "success",
        "user": user.json()
    }


def get_user(id: uuid.UUID):
    if id in loggedInUsers:
        return loggedInUsers[id]
    else:
        return None


def do_action(id: uuid.UUID, action: Callable[[User], None]):
    user = get_user(id)
    if user:
        action(user)
        return {
            "status": "success"
        }
    else:
        return {
            "status": "error",
            "message": "User not logged in"
        }


def do_action_with_return(id: uuid.UUID, action: Callable[[User], None]):
    user = get_user(id)
    if user:
        return {
            "status": "success",
            "data": action(user)
        }
    else:
        return {
            "status": "error",
            "message": "User not logged in"
        }


def get_servers_info(servers: List[AternosServer]):
    return [ServerInfo(servid=server.servid, address=server.address) for server in servers]



@app.get("/servers")
def servers(id: uuid.UUID):## return server 
    return do_action_with_return(id, lambda user: get_servers_info(user.aternos.servers))



@app.post("/start")
def start(server: Server):
    return do_action(server.userId, lambda user: user.aternos.get_server(server.serverId).start())


@app.post("/stop")
def stop(server: Server):
    return do_action(server.userId, lambda user: user.aternos.get_server(server.serverId).stop())


@app.post("/restart")
def restart(server: Server):
    return do_action(server.userId, lambda user: user.aternos.get_server(server.serverId).restart())


@app.post("/status")
def status(server: Server):
    return do_action(server.userId, lambda user: user.aternos.get_server(server.serverId).status())


def _logout(id: uuid.UUID):
    del loggedInUsers[id]


@app.post("/logout")
def logout(user: User):
    return do_action(user.id, lambda user: _logout(user.id))
    # if user.id in loggedInUsers:
    #     del loggedInUsers[user.id]
    #     return {
    #         "status": "success"
    #     }
    # else:
    #     return {
    #         "status": "error",
    #         "message": "User not logged in"
    #     }
