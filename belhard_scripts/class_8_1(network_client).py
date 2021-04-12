import socket
HOST = "127.0.0.1" # удаленный компьютер (localhost)
PORT = 33333 # порт на удаленном компьютере
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
sock.send("ПАЛИНДРОМ".encode())
result = sock.recv(1024)
result=result.decode()
sock.close()
print("Получено:", result)