import subprocess
import time


class Processes:
    def __init__(self, clients):
        self.clients = clients

    def start_server_clients(self):
        processes = []
        while True:
            action = input('Введите нужную команду: \nstart - запустить сервер и клиентов,\n'
                           'close - закрыть все окна,\nexit - выход\n')
            if action == 'start':
                processes.append(subprocess.Popen('python server_main.py', creationflags=subprocess.CREATE_NEW_CONSOLE))
                time.sleep(1)
                for i in range(1, self.clients + 1):
                    processes.append(subprocess.Popen(f'python client.py -n test{i}',
                                                      creationflags=subprocess.CREATE_NEW_CONSOLE))
            elif action == 'close':
                while processes:
                    client = processes.pop()
                    client.kill()
            elif action == 'exit':
                break


def main():
    processes = Processes(3)
    processes.start_server_clients()


if __name__ == '__main__':
    main()
