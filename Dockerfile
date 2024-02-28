FROM python:3.8

ENV HOME /root 
WORKDIR /root 

COPY . .

# Download dependancies 
RUN pip3 install -r requirements.txt 

#opens port 8080
EXPOSE 8080

CMD python3 -u server.py