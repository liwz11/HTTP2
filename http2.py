import os, sys, requests, zipfile, csv, re, json, signal, time
from hyper import HTTPConnection
from hyper import tls

def unzip(filepath):
    zf = zipfile.ZipFile(filepath, 'r')
    for file in zf.namelist():
        zf.extract(file, r'.')
    zf.close()

def download_top1m(url, flag):
    zipfilename = url.split('/')[-1]
    csvfilename = zipfilename[:-4]

    if (flag == 1) or (os.path.exists(zipfilename) == False):
        r = requests.get(url)
        f = open(zipfilename, "wb")
        f.write(r.content)
        f.close()

        unzip(zipfilename)

    return zipfilename, csvfilename

def init_headers(csvfilename, headers):
    f = open(csvfilename, 'r')
    csv_data = csv.reader(f)
    first_row = next(csv_data)
    rows = [row for row in csv_data]
    f.close()

    f = open(csvfilename, 'wb')
    writer = csv.writer(f)
    writer.writerow(headers)
    if first_row[0] != headers[0]:
        writer.writerow(first_row)
    writer.writerows(rows)
    f.close()

def add_header(csvfilename, header, value):
    f = open(csvfilename, 'r')
    csv_data = csv.reader(f)
    headers = next(csv_data)
    rows = [row for row in csv_data]
    f.close()

    if headers.count(header) == 0:
        headers.append(header)
        for row in rows:
            row.append(value)
            rows[int(row[0])-1] = row

    f = open(csvfilename, 'wb')
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(rows)
    f.close()

def url_check_http2(url):
    conn = HTTPConnection(url, port=443, secure=True, ssl_context=tls.init_context(cert_path=None, cert=None))
    try:
        r = conn.request('GET', '/')
        if r == None:
            return 3
        else:
            return 1
    except:
        return 5

def url_check_host(url):
    www_url = 'www.' + url
    p = os.popen('host -t A ' + www_url)
    www_res = p.read()
    p.close()
    
    if (www_url + ' is an alias for ') in www_res:
        return 1, www_url
    elif (www_url + ' has address ') in www_res:
        return 0, www_url
    else:
        p = os.popen('host -t A ' + url)
        res = p.read()
        p.close()

        if (url + ' is an alias for ') in res:
            return 1, url
        elif (url + ' has address ') in res:
            return 0, url
        else:
            return -1, rul


def sigint_handler(signum, frame):
    global is_sigint_up
    is_sigint_up = True
    print 'Catch Ctrl+C!'

def sigalarm_handler(signum, frame):
    print 'Catch an alarm!'

is_sigint_up = False

if __name__ == '__main__':
    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGALRM, sigalarm_handler)

    url = 'http://s3.amazonaws.com/alexa-static/top-1m.csv.zip'
    zipfilename, csvfilename = download_top1m(url, 0)
    if os.path.exists(csvfilename) == False:
        unzip(zipfilename)
        print 'init_headers...'
        init_headers(csvfilename, ['rank', 'domain'])
        print 'add_header...'
        add_header(csvfilename, 'http2','-1')

    f = open(csvfilename, 'r')
    csv_data = csv.DictReader(f)
    rows = [row for row in csv_data]
    f.close()

    for row in rows:
        if is_sigint_up or (int(row['rank']) % 500 == 0):
            f = open(csvfilename, 'wb')
            writer = csv.DictWriter(f, fieldnames=['rank', 'domain', 'http2'])
            writer.writeheader()
            writer.writerows(rows)

            if is_sigint_up:
                break

        if row['http2'] != '-1':
            continue

        (r, url) = url_check_host(row['domain'])
        
        if r == -1:
            r1 = 1
        else:
            r1 = url_check_http2(url)
            
        row['http2'] = r + r1
        rows[int(row['rank'])-1] = row

        print row['rank'] + ' ' + row['domain'] + ': ' + str(r) + ' + ' + str(r1) + ' = ' + str(row['http2'])


