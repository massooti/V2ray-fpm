from app import app
from flask import render_template, url_for, request
import json
import subprocess
from urllib.parse import unquote
from app.models import v2rayConfig, AlchemyEncoder, Others
from app import db
from app.v2rayControl.vmess2json import gen_client
from app.models import Parse, subscription
import re
import urllib

'''
Get v2ray running status
'''


def get_status():
    output = subprocess.Popen("service v2ray status | grep Active | awk '{print $2}'", shell=True,
                              stdout=subprocess.PIPE).communicate()[0].strip().decode('utf-8')
    if output == "active":
        return "on"
    else:
        return "off"


'''
run v2ray
'''


def start():
    subprocess.Popen(
        "kill $(ps -ef|grep 'v2ray -config'|awk '{print$1}')", shell=True)

    subprocess.Popen("v2ray -config /etc/v2ray/config.json &", shell=True)
    return "OK"


'''
stop v2ray
'''


def stop():
    subprocess.Popen(
        "kill $(ps -ef|grep 'v2ray -config='|awk '{print$1}')", shell=True)
    return "OK"


'''
restart v2ray
'''


def restart():
    subprocess.Popen(
        "kill $(ps -ef|grep 'v2ray -config'|awk '{print$1}')", shell=True)
    subprocess.Popen("v2ray -config /etc/v2ray/config.json &", shell=True)
    return "OK"


'''
Convert the vmess link to the config format of the database
'''


def json2config(data, sub_url=""):
    print(data)
    v2 = v2rayConfig(
        add=data['add'],
        aid=data['aid'],
        host=data['host'],
        id=data['id'],
        net=data['net'],
        path=data['path'],
        port=data['port'],
        ps=data['ps'],
        tls=data['tls'],
        type=data['type'],
        encrypt='auto',
        mux='off',
        status="off",
        sub=sub_url
    )
    return v2


'''
message processing part
'''


def set_message(code=200, url=""):
    if code == 200:
        return {
            "code": code,
            "status": "Success",
            "url": url
        }
    else:
        return {
            "code": code,
            "status": "Failure",
            "url": url
        }


def get_info():
    with open("config/v2ray/others.json") as v2ray_config:
        json_content = json.load(v2ray_config)
        json_dump = json.dumps(json_content)

    return json_dump


'''
Main interface routing part
'''


@app.route('/', methods=["GET", "POST"])
@app.route('/index', methods=["GET", "POST"])
def index():
    page = request.args.get('page', 1, type=int)
    configs = v2rayConfig.query.order_by(v2rayConfig.status.desc()).paginate(
        page, app.config['PER_PAGE'], False)
    next_url = url_for('index', page=configs.next_num) \
        if configs.has_next else None
    prev_url = url_for('index', page=configs.prev_num) \
        if configs.has_prev else None
    return render_template('index.html', v2rayconfigs=configs.items, title="configuration options", next_url=next_url,
                           prev_url=prev_url)


@app.route('/config', methods=["GET"])
def config():
    num = request.args.get('num')
    editConfig = v2rayConfig.query.filter(v2rayConfig.num == num).first()
    return render_template('config.html', v2ray=editConfig, title="Add/modify connection")


@app.route('/subscription')
def Subscription():
    sub = subscription.query.order_by(subscription.num)
    return render_template('subscription.html', title="subscription management", subscriptions=sub)


@app.route('/log')
def log():
    return render_template('log.html', title="run log")


@app.route('/others')
def others():
    otherConfig = Others.get_all()
    socks5 = otherConfig['INBOUNDS'].split(',')[0][6:]
    http = otherConfig['INBOUNDS'].split(',')[1][5:]
    return render_template('others.html', title="Rest of configuration", config=otherConfig, socks5=socks5, http=http)


@app.route('/get_access_log')
def get_access_log():
    try:
        with open(Others.get_all()['V2RAY_ACCESS_LOG']) as f:
            content = f.read().split("\n")
            min_length = min(20, len(content))
            content = content[-min_length:]
            string = ""
            for i in range(min_length):
                string = string + content[i] + "<br>"
        return string
    except PermissionError as e:
        return " Permission denied "


@app.route('/get_error_log')
def get_error_log():
    try:
        with open(Others.get_all()['V2RAY_ERROR_LOG']) as f:
            content = f.read().split("\n")
            min_length = min(20, len(content))
            content = content[-min_length:]
            string = ""
            for i in range(min_length):
                string = string + content[i] + "<br>"
        return string
    except PermissionError as e:
        return " Permission denied "


'''
The api part, maybe it should be packaged together, lazy
'''
re_word = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'


@app.route('/api/addSubscription', methods=["GET", "POST"])
def addSubscription():
    data = json.loads(request.get_data(as_text=True))
    print(data)
    # Check whether the subscription address is legal
    if not re.findall(re_word, data['addr']):
        return set_message(400)
    sub = subscription(
        addr=data['addr'],
        remarks=data['remarks']
    )
    # Find out if this subscription address already exists
    find = subscription.query.filter(subscription.addr == data['addr']).first()
    if find is not None:
        return set_message(400)
    print("1")
    db.session.add(sub)
    db.session.commit()
    return set_message(200)


@app.route('/api/deleteSub', methods=["GET", "POST"])
def deleteSub():
    data = request.get_data(as_text=True)
    num = data.split('=')[1]
    deleteConfig = subscription.query.filter(subscription.num == num).first()
    configs = v2rayConfig.query.filter(v2rayConfig.sub == deleteConfig.addr)
    for i in configs:
        db.session.delete(i)
    db.session.delete(deleteConfig)
    db.session.commit()

    return set_message(200)


@app.route('/api/editSubscription', methods=["GET", "POST"])
def editSubscription():
    data = json.loads(request.get_data(as_text=True))
    print(data)
    modifyConfig = subscription.query.filter(
        subscription.num == data['num']).first()
    if modifyConfig is None:
        return set_message(400)
    modifyConfig.addr = data['addr']
    modifyConfig.remarks = data['remarks']
    db.session.commit()
    return set_message(200)


@app.route('/api/updateSub', methods=["GET", "POST"])
def updateSub():
    data = request.get_data(as_text=True)
    num = data.split('=')[1]
    updateConfig = subscription.query.filter(subscription.num == num).first()
    sub_url = updateConfig.addr
    print(sub_url)
    try:
        print("Reading from subscribe ...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}
        req = urllib.request.Request(url=sub_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            _subs = response.read()
            result = Parse.parse_subscription(_subs)
    except Exception as e:
        return set_message(400)
    if result is None:
        return set_message(400)
    print(result)
    need_stop = v2rayConfig.query.filter(v2rayConfig.status == "on").first()

    if need_stop is not None:
        stop()
    old_sub = v2rayConfig.query.filter(v2rayConfig.sub == sub_url)
    for i in old_sub:
        db.session.delete(i)
    for i in result:
        try:
            v2 = json2config(i, sub_url)
            db.session.add(v2)
        except KeyError:
            continue
    db.session.commit()
    return set_message(200, url_for('index'))


@app.route('/api/generate_config', methods=['GET', 'POST'])
def generate_config():
    data = json.loads(request.get_data(as_text=True))
    print(data)

    if 'num' in data.keys():
        saveConfig = v2rayConfig.query.filter(
            v2rayConfig.num == data['num']).first()
        saveConfig.id = data['uuid']
        saveConfig.add = data['addr']
        saveConfig.port = data['port']
        saveConfig.aid = data['alterId']
        saveConfig.encrypt = data['encrypt']
        saveConfig.type = data['fake']
        saveConfig.path = data['path']
        saveConfig.tls = data['tls']
        saveConfig.mux = data['mux']
        saveConfig.ps = data['remarks']
        saveConfig.net = data['trans']
        saveConfig.host = data['host']
        saveConfig.status = data['status']
    else:

        v2 = v2rayConfig(
            id=data['uuid'],
            add=data['addr'],
            port=data['port'],
            aid=data['alterId'],
            encrypt=data['encrypt'],
            type=data['fake'],
            path=data['path'],
            tls=data['tls'],
            mux=data['mux'],
            status=data['status'],
            ps=data['remarks'],
            net=data['trans'],
            host=data['host']
        )
        db.session.add(v2)
    db.session.commit()
    return set_message(200, url_for('index'))


@app.route('/api/deleteById', methods=["GET", "POST"])
def deleteById():
    data = request.get_data(as_text=True)
    num = data.split('=')[1]
    deleteConfig = v2rayConfig.query.filter(v2rayConfig.num == num).first()
    db.session.delete(deleteConfig)
    db.session.commit()
    return set_message(200)


@app.route('/api/editById', methods=["GET", "POST"])
def editById():
    data = request.get_data(as_text=True)
    num = data.split('=')[1]
    return set_message(200, url_for('config', num=num))


@app.route('/api/start_service', methods=['POST', "GET"])
def start_service():
    try:
        data = request.get_data(as_text=True)
        print(v2rayConfig.status, type(v2rayConfig.status),
              (v2rayConfig.status == "on"), "\n\n\n", v2rayConfig)
        num = data.split('=')[1]
        startConfig = v2rayConfig.query.filter(v2rayConfig.status == "on")
        for i in startConfig:
            i.status = "off"
        startConfig = v2rayConfig.query.filter(v2rayConfig.num == num).first()
        myjson = json.dumps(startConfig, cls=AlchemyEncoder)

        gen_client(json.loads(myjson))
        startConfig.status = "on"
        db.session.commit()
        restart()
        return set_message(200)
    except PermissionError as e:
        return set_message(400)


@app.route('/api/stop_service', methods=['POST', "GET"])
def stop_service():
    data = request.get_data(as_text=True)
    print(data)
    num = data.split('=')[1]
    stopConfig = v2rayConfig.query.filter(v2rayConfig.num == num).first()
    if stopConfig.status == "off":
        return set_message(400)
    stopConfig.status = "off"
    db.session.commit()
    stop()
    return set_message(200)


@app.route('/api/vmess2config', methods=["POST", "GET"])
def vmess2config():
    try:
        data = request.get_data(as_text=True)
        data = data.split('=')[1]
        data = unquote(data)
        data = Parse.parseVmess(data)
    except Exception as e:
        return set_message(400)
    v2 = json2config(data)
    db.session.add(v2)
    db.session.commit()
    return set_message(200)


@app.route('/api/changeOthers', methods=["GET", "POST"])
def changeOthers():
    data = json.loads(request.get_data(as_text=True))
    print(data)
    # = "socks:10808,http:10809"
    socks = int(data['socks5'])
    http = int(data['http'])

    if socks <= 0 or socks > 65535:
        return set_message(400)
    if http <= 0 or http > 65535:
        return set_message(400)
    route = data['route']
    strategy = data['strategy']

    Others.set_info('INBOUNDS', "socks:" + str(socks) +
                    "," + "http:" + str(http))

    if route == "global":
        Others.set_info('RULES', 'all')
    elif route == "Bypass LAN address":
        Others.set_info('RULES', 'bpL')
    elif route == "Bypass mainland address":
        Others.set_info('RULES', 'bpA')
    else:
        Others.set_info('RULES', 'bpLAA')

    Others.set_info('DOMAINSTRATEGY', strategy)
    restart()
    return set_message(200, url_for('index'))
