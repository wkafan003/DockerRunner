import asyncio
import json
from typing import Optional, List
from loguru import logger
from pydantic import BaseModel
from enum import Enum, IntEnum
import subprocess


class StateEnum(IntEnum):
    not_init = 0
    building = 1
    ready_to_run = 2
    running = 3
    stopped = 4
    removed = 5
    error = 6


class Container(BaseModel):
    image_name: str
    image_uri: str
    container_name: str
    state: StateEnum = StateEnum.not_init
    log: str = 'Not init'

    async def build_image(self):
        self.state = StateEnum.building
        self.log = 'Building container'
        proc: asyncio.subprocess = None
        stderr: bytes = None
        try:
            proc = await asyncio.create_subprocess_shell(
                f'docker build {self.image_uri} -t {self.image_name}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0:
                self.state = StateEnum.ready_to_run
                self.log = stdout.decode('utf-8')
            else:
                self.state = StateEnum.error
                self.log = stderr.decode('utf-8')
        except Exception as e:
            self.state = StateEnum.error
            if proc is not None and proc.returncode != 0 and stderr:
                self.log = stderr.decode('utf-8')
            else:
                self.log = 'Build error'

        # return proc.returncode, stdout, stderr

    async def stop_container(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                f'docker stop {self.container_name}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0:
                self.state = StateEnum.stopped
                self.log = 'Successful stop'
            else:
                raise Exception('Keycode not 0')
        except:
            self.state = StateEnum.error
            self.log = 'Stop error'

    async def remove_container(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                f'docker rm {self.container_name}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0:
                self.state = StateEnum.removed
                self.log = 'Successful remove'
            else:
                raise Exception('Remove keycode not 0')
        except:
            self.state = StateEnum.error
            self.log = 'Stop error'

    async def run_container(self, ports: Optional[List[int]] = None, entrypoint: Optional[str] = None):
        # Праблем(( с установкой состояния, держать процесс постоянно стремно
        if entrypoint is None:
            entrypoint = ''
        try:
            ports_s = ''
            if ports:
                for i in range(0, len(ports), 2):
                    ports_s += f'-p {ports[i]}:{ports[i + 1]}'

            # proc = await asyncio.create_subprocess_shell(
            #     f'docker run {ports_s} -P --name {self.container_name} {self.image_name} {entrypoint}')
            p = subprocess.Popen(
                f'bash -c "docker run {ports_s} -P --name {self.container_name} {self.image_name} {entrypoint}"',
                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.log = 'Starting'
        except:
            self.state = StateEnum.error
            self.log = 'Run error'

    async def force_run(self, ports: Optional[List[int]] = None, entrypoint: Optional[str] = None):
        await self.stop_container()
        await self.remove_container()
        await self.build_image()
        await self.run_container(ports=ports, entrypoint=entrypoint)
    async def force_delete(self):
        await self.stop_container()
        await self.run_container()
    async def check_state(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                f'docker inspect {self.container_name}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0:
                j = json.loads(stdout.decode('utf-8'))
                j = j[0]['State']
                if j['ExitCode'] != 0:
                    self.state = StateEnum.error
                    self.log = j['Error']
                    return
                if j['Running']:
                    proc2 = await asyncio.create_subprocess_shell(
                        f'docker logs {self.container_name}',
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE)
                    stdout2, stderr2 = await proc2.communicate()
                    if proc2.returncode == 0:
                        self.state = StateEnum.running
                        self.log = stdout2.decode('utf-8') + stderr2.decode('utf-8')
                        # self.log = ss.decode('utf-8')
                    else:
                        raise Exception
                    return
                if j['Paused']:
                    self.state = StateEnum.stopped
                    self.log = 'Container stopped'
                self.state = StateEnum.not_init
                self.log = 'Not init'
                return
            else:
                self.state = StateEnum.error
                self.log = stderr.decode('utf-8')
        except Exception as e:
            self.state = StateEnum.error
            self.log = 'Inspect error'

# name='kekb999888c-5efb-11eb-8ab9-ebc0dacd7f77'
# c = Container(image_name=name, image_uri='./dockers/'+name, container_name=name)


# async def keks():
# await c.stop_container()
# print(c)
# await c.remove_container()
# print(c)
# await c.build_image()
# print(c)
# await c.force_run(ports=[8001,8000])
# print(c)
# await c.check_state()
# print(c)


# asyncio.run(keks())
# print(c)
