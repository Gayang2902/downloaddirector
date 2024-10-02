# 청크 단위로 파일을 쪼개서 실시간으로 원격 서버에 파일을 스트리밍

import paramiko
import requests
import os
import sys
from tqdm import tqdm

class Connection:
    def __init__(self):
        with open('/Users/bink/code/downloaddirector/dir.conf', 'r') as conf:
            datas = conf.readlines()
            self.remote_host = (datas[4].split('=')[1])[:-1]
            self.remote_user = (datas[5].split('=')[1])[:-1]
            self.remote_dir = (datas[6].split('=')[1])[:-1]
            print(f'HOST: {self.remote_host}\nUSER: {self.remote_user}\nDIR: {self.remote_dir}')

    def connect(self):
        # ssh 연결
        self.ssh = paramiko.SSHClient()
        # known host 등의 정책을 자동 설정
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect \
                (hostname=self.remote_host, username=self.remote_user)
        try:
            # sftp 연결
            self.sftp = self.ssh.open_sftp()
            print('Connection success')
        except Exception as e:
            print('Connection fail')

    def download(self, url, chunk_size=1024):
        # 원격지 경로 설정
        filename = input('Input filename: ')
        remote_path = os.path.join(self.remote_dir, filename)
        remote_file = self.sftp.file \
                                (filename=remote_path, mode="wb")
        # 로컬, URl로부터 파일을 다운로드
        # 파일은 stream 방식으로 청크 단위로 분할하여 가져옴
        response = requests.get(url, stream=True)
        # 프로그레스바
        total = int(response.headers.get('content-length', 0))
        #reference> https://gist.github.com/yanqd0/c13ed29e29432e3cf3e7c38467f42f51
        with open(filename, 'wb') as file, tqdm(
            desc=filename,
            total=total,
            unit='iB',
            unit_scale=True,
            unit_divisor=chunk_size,
        ) as bar:
            for data in response.iter_content(chunk_size=chunk_size):
                size = file.write(data)
                bar.update(size)
                # 원격지에 스트리밍
                if data:
                    remote_file.write(data)

        remote_file.close()

    def close(self):
        self.sftp.close()
        self.ssh.close()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('Usage: python stream.py <file_url>')
        sys.exit(-1)

    c = Connection()
    c.connect()
    c.download(sys.argv[1])
    c.close()
