import time
import os
from enum import Enum

import uvicorn
import aiofiles as aiof
import subprocess
import asyncio
import uuid
from shutil import copyfile
from pathlib import Path
from typing import Iterable, List, Dict
from fastapi import FastAPI, Query, UploadFile, File, HTTPException
from fastapi.logger import logger
from pydantic import BaseModel, Field

from custom_logging import CustomizeLogger
from utils import dockerfile_template
from container import Container, StateEnum

app = FastAPI()
# app.containers: Dict[str, Container] = {}
app.containers = {}
app.logger = CustomizeLogger.make_logger(Path(__file__).with_name('logginc_config.json'))


class Person(BaseModel):
    name: str = Field('Kek3')


class Env(str, Enum):
    conda = 'conda'
    virtualenv = 'virtualenv'


@app.get('/containers/{container_name}')
async def get_status(container_name: str, log: bool = False, inspect: bool = False):
    c: Container = app.containers.get(container_name, None)
    if c is None:
        raise HTTPException(status_code=404, detail="Item not found")

    if inspect:
        await c.check_state()

    response = {'status': c.state.name}
    if log:
        response['log'] = c.log
    app.logger.info(f'Get info {container_name} with {"logs" if log else ""} {"inspect" if inspect else ""}')
    return response


@app.delete('/containers/{container_name}')
async def rm_container(container_name: str):
    c: Container = app.containers.get(container_name, None)
    if c is None:
        raise HTTPException(status_code=404, detail="Item not found")
    asyncio.create_task(c.force_delete())
    app.containers.pop(container_name)
    app.logger.info(f'Remove container {container_name}')
    return {'response': f'Successfully remove container {container_name}'}


@app.get('/containers')
async def containers_list():
    app.logger.info(f'Get containers name - {len(app.containers)} elements')
    return {'container_names': list(app.containers.keys())}


@app.post('/containers')
async def run_new_container(entrypoint_file: str = 'main.py', env: Env = Env.virtualenv, ports: List[str] = None,
                            files: List[UploadFile] = File(...)):
    # file = files[0]
    name = 'kek' + str(uuid.uuid1())
    path = f'./dockers/{name}'
    app.logger.info(name)
    if ports and ports[0] != '':
        ports = [int(p) for p in ports[0].split(',')]

    Path(path).mkdir(parents=True, exist_ok=True)
    dependencies = 'default'
    for file in files:
        if file.filename == 'environment.yml':
            dependencies = file.filename
        elif file.filename == 'requirements.txt' and dependencies != 'environment.yml':
            dependencies = file.filename
        data = await file.read()
        async with aiof.open(f'{path}/{file.filename}', "wb+") as out:
            await out.write(data)
            await out.flush()

    # os.system('docker')
    await dockerfile_template('Dockerfile', env=env.value, dependencies=dependencies,
                              out_file=path + '/Dockerfile', entrypoint_file=entrypoint_file)
    # copyfile('./requirements.txt', f'{path}/requirements.txt')
    copyfile('./.dockerignore', f'{path}/.dockerignore')
    c = Container(image_name=name, image_uri=path, container_name=name)
    app.containers[name] = c
    asyncio.create_task(c.force_run(ports=ports))
    app.logger.info(f'Create new container {name}')
    return {'container_name': name}
    # return {'filenames': [file.filename for file in files]}


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')
    # uvicorn.run('main:app', host='0.0.0.0', port=8000,reload=True, log_level='info')
