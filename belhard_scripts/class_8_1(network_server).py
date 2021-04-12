import socket
def do_something(x):
    x=x[::-1]
    return x
HOST = "127.0.0.1" # localhost
PORT = 33333
srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.bind((HOST, PORT))
while 1:
    print("Слушаю порт 33333")
    srv.listen(1)
    sock, addr = srv.accept()
    while 1:
        pal = sock.recv(1024).decode()
        if not pal:
            break
        print("Получено от {} - {}".format(addr, pal))
        lap = do_something(pal)
        print("Отправлено {} - {}".format(addr, lap))
        sock.send(lap.encode())
    sock.close()

