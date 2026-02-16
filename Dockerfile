# Naudojame oficialų Python atvaizdą
FROM python:3.9-slim

# Nustatome aplinkos kintamuosius
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Sukuriame ir nustatome darbo direktoriją
WORKDIR /app

# Įdiegiame priklausomybes
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Kopijuojame projekto kodą
COPY . /app/

# Atidarome prievadą
EXPOSE 8000
