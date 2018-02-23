import logging
import socket
import sys
import ssl

def parse_url(url):

        url_split = url.split('/' ,3)
        scheme = url_split[0]
        host = url_split[2].split(':')[0]
        try:
            path = '/' + url_split[3]
        except:
            path = '/'
        if scheme == 'https:':
            is_https = True
            port = 443
        else:
            is_https = False
            port = 80
        try:
            port = int(url_split[2].split(':')[1])
        except:
            port = port
        return(host,path,port,is_https,True)


def read_buffer(sock):
    buff = b''
    while True:
        recv = sock.recv(1024)
        if not recv:
            break
        buff += recv
    return buff

def parse_Header(header):
    is_chuncked = False
    header_str = header.decode()
    header_split = header_str.split('\r\n')
    return_status = int(header_split[0].split(' ')[1])
    if return_status == 200:
        for line in header_split[1:]:
            (k,v) = line.split(':',1)
            if k == 'Transfer-Encoding' and (v == 'chunked' or v == ' chunked'):
                return (True,'', True)
            if k == 'Content-Length':
                return (False, int(v), True)
    return ('','',False)

def is_chuncked_body(body):
    chunked_body = b''
    while True:
        (chunk_size, body) = body.split(b'\r\n',1)
        chunk_size = chunk_size.decode().split(';',1)[0]
        chunk_size = int(chunk_size, 16)
        if chunk_size == 0:
            break
        chunked_body += body[:chunk_size]
        body = body[chunk_size+2:]
    return chunked_body

def check_for_Chunked_Encoding(buff):
    (header,body) = buff.split(b'\r\n\r\n',1)
    (is_chuncked, value, url_status) = parse_Header(header)
    if url_status == False:
        return None
    if is_chuncked:
        return is_chuncked_body(body)
    else:
        return body[:value]
   
def retrieve_url(url):
    (host,path,port,is_https,url_status) = parse_url(url)

    if url_status == False:
        return None

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (host, port)
    request_header = 'GET ' +  path +' HTTP/1.1\r\nHost: ' + host +'\r\nConnection: close\r\n\r\n'
    response = b''
    if is_https:
        try:
            ss = ssl.create_default_context(ssl.Purpose.SERVER_AUTH).wrap_socket(client_socket, server_hostname=host)
            ss.connect(server_address)
        except:
            return None
        ss.send(request_header.encode())
        response = check_for_Chunked_Encoding(read_buffer(ss))
        ss.close()
        return response
    else:
        try:
            client_socket.connect(server_address)
        except:
            return None
        client_socket.send(request_header.encode())
        response = check_for_Chunked_Encoding(read_buffer(client_socket))
        client_socket.close()
        return response
