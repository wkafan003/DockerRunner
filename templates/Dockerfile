{% if env=='conda' %}
#FROM continuumio/anaconda3
FROM continuumio/miniconda3
{%  elif env=='virtualenv' %}
FROM python:3.8.7-slim-buster
{% endif %}
WORKDIR ./app

{% if env=='conda' %}
RUN conda update -y -q -n base -c defaults conda
    {% if dependencies=='environment.yml' %}
COPY environment.yml ./
RUN conda env create -f environment.yml &&\
echo "source activate /opt/conda/envs/$(head -1 ./environment.yml | cut -d' ' -f2)" > ~/.bashrc
    {% else %}
RUN conda create -y -q -c conda-forge -n default_env python={{python_version}}
        {% if dependencies=='requirements.txt'%}
COPY requirements.txt ./
RUN conda install --force-reinstall -y -q --name default_env -c conda-forge --file requirements.txt &&\
echo "source activate /opt/conda/envs/defauult_env" > ~/.bashrc
        {% endif %}
    {% endif %}
{% elif env=='virtualenv' %}
    {% if dependencies=='requirements.txt' %}
COPY requirements.txt ./
RUN pip install -r ./requirements.txt
    {% endif %}
{% endif %}
COPY . ./

{% if env=='conda' %}
    {% if dependencies=='environment.yml' %}
CMD ["sh","-c","/opt/conda/envs/$(head -1 ./environment.yml | cut -d' ' -f2)/bin/python ./{{entrypoint_file}}"]
    {% else %}
CMD ["sh","-c","/opt/conda/envs/default_env/bin/python ./{{ entrypoint_file }}"]
    {% endif %}
{% else %}
CMD ["python","./{{ entrypoint_file }}"]
{% endif %}


{% if ports %}
EXPOSE {% for port in ports %}{{port}} {% endfor %}
{% endif %}
