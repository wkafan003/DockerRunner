import os
import asyncio
import aiofiles as aiof
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader
from loguru import logger

from container import Container

THIS_DIR = os.path.dirname(os.path.abspath(__file__)) + '/templates'
j2_env = Environment(loader=FileSystemLoader(THIS_DIR),
                     trim_blocks=True, lstrip_blocks=True)


async def dockerfile_template(name: str, ports: Optional[List[int]] = None, env: str = 'virtualenv',
                              python_version: str = '3.8',
                              dependencies: Optional[str] = None, out_file: Optional[str] = None,
                              entrypoint_file: str = 'main.py'):

    s = j2_env.get_template('Dockerfile').render(ports=ports, env=env, dependencies=dependencies, name=name,
                                                 python_version=python_version, entrypoint_file=entrypoint_file)

    logger.info(f'Template dockerfile,ports={" ".join([str(p) for p in ports]) if ports else "None"},env={env},'
                f'dependencies={dependencies},out_file={out_file},entrypoint={entrypoint_file}')
    if out_file:
        async with aiof.open(out_file, "w+") as out:
            await out.write(s)
            await out.flush()

        # with open(out_file, 'w') as file:
        #     file.write(s)
    else:
        return s
