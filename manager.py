import threading
from time import sleep
import pexpect
import os
import json
from mcstatus import MinecraftServer


class ServerEncoder(json.JSONEncoder):
    def default(self, obj):
        if not isinstance(obj, Server):
            return super(ServerEncoder, self).default(obj)
        return obj.__dict__

class Server(object):
    def __run__(self):
        while self.child.isalive():
            try:
                line = self.child.readline().decode("UTF-8").replace("\n","")
                print(self.name,line)
                if "Done" in line:
                    print("Server is UP!")
            except Exception:
                self.sendCommand("/n")
                self.child.readline()
                self.child.readline()
        print(self.name, "has stopped!")

    def __init__(self, folder, name, ram=512, args="", jar="minecraft.jar"):
        self.name = name
        self.ram = ram
        self.args = args
        self.folder = folder + name + "/"
        self.jar = jar
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
    def __init__(self, config):
        self.name = config["name"]
        self.ram = config["ram"]
        self.args = config["args"]
        self.folder = config["folder"]
        self.jar = config["jar"]

    def start(self):
        print("server has started")
        self.child = pexpect.spawn("java -jar " + "-Xms%sM" % self.ram + " " + self.jar + " " + self.args, cwd=self.folder)
        self.reader = threading.Thread(target=self.__run__)
        self.reader.daemon = True
        self.reader.start()

    def sendCommand(self, command):
        self.child.sendline(command)

    def isRunning(self):
        return self.child.isalive()

    def wait(self):
        if self.child.isalive():
            return self.child.wait()

    def getProperties(self):
        propfile = self.folder + "server.properties"
        data = {}
        if (os.path.isfile(propfile)):
            with open(propfile, "r") as file:
                lines = file.readlines()
                for line in lines:
                    line = line.replace("\n","")
                    if not line.startswith('#') and "=" in line:
                        linedata = line.split("=")
                        data[linedata[0]]=linedata[1]
        return data
    def getStatus(self):
        prop = self.getProperties()
        port = prop["server-port"]
        host = prop["server-ip"]
        if not host:
            host = "127.0.0.1"
        print(port, host)
        return MinecraftServer.lookup(host + ":" + port).status()

class serverPool(object):
    servers = {}

    def __init__(self, folder):
        self.folder = folder
        self.configfile = folder + "servers.json"
        if os.path.isfile(self.configfile):
            with open(self.configfile, "r") as file:
                servers = json.load(file)
                for server in servers:
                    self.addServerConfig(servers[server])
        else:
            self.__save__config__()

    def __save__config__(self):
        with open(self.configfile, "w", encoding="UTF-8") as file:
            json.dump(self.servers,file, ensure_ascii=True, cls=ServerEncoder, indent=4)

    def addServer(self, server):
        self.servers[server.name]= server
        print(self.servers, server)
        self.__save__config__()
    def addServerConfig(self, config):
        self.addServer(Server(config))

    def startall(self):
        for server in self.servers.values():
            server.start()

    def waitall(self):
        for server in self.servers.values():
            server.wait()
    def getServer(self, name):
        return self.servers[name]


serverFolder = "./servers/"

if __name__ == "__main__":

    pool = serverPool(serverFolder)
    server = pool.getServer("server1")
    server.start();
    while (True):
        try:
            sleep(10)
            print("Trying to get status!!")
            status = server.getStatus()
            print(status.players.online, server.players.max)
        except Exception:
            continue
