# Naudojame oficialų Python atvaizdį
FROM python:3.9-slim

# Nustatome aplinkos kintamuosius
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install nodejs and npm
RUN apt-get update && apt-get install -y nodejs npm

# Sukuriame ir nustatome darbo direktoriją
WORKDIR /app

# Įdiegiame Python priklausomybes
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Įdiegiame npm priklausomybes
COPY package.json /app/
RUN npm install

# Kopijuojame projekto kodą
COPY . /app/

# Atidarome prievadą
EXPOSE 8000
