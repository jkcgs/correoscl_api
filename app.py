from flask import jsonify
from flask import Flask
from bs4 import BeautifulSoup
import requests
import re

pat_code = re.compile('^[A-Za-z0-9]{1,30}$')
data_url = 'http://seguimientoweb.correos.cl/ConEnvCorreos.aspx'
app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'el henry se la come xd'


@app.route('/<code>')
def track_info(code):
    return get_data(code)


@app.errorhandler(500)
def ise(e):
    return jsonify(error=500, message='internal server error'), 500


@app.errorhandler(404)
def page_not_found(e):
    return jsonify(error=404, message='page not found'), 404


def get_data(code):
    # Validate tracking code format
    if not pat_code.match(code):
        return jsonify(error=400, message='invalid code'), 400

    # Convert AliExpress long tracking code
    if len(code) == 26 and code.isnumeric():
        code = 'ALS' + code[15:-3]

    # Retrieve and parse html data
    resp = requests.post(data_url, {'obj_key': 'Cor398-cc', 'obj_env': code})
    dom = BeautifulSoup(resp.text, 'html.parser')

    # Code does not exist on upstream
    if len(dom.find_all(attrs={'class': 'envio_no_existe'})) > 0:
        return jsonify(error=404, message='code not found'), 404

    # Return results as JSON
    return jsonify({
        'info': parse_info(dom),
        'entries': parse_entries(dom)
    })


def parse_info(dom):
    info_cont = dom.find(class_='datosgenerales')
    if info_cont is None:
        return None

    keys = {3: 'receiver', 5: 'datetime', 7: 'rut'}
    return {keys[i]: r.text.strip() for i, r in enumerate(info_cont.find_all('td')) if i % 2 != 0 and i != 1}


def parse_entries(dom):
    return [parse_entry_row(r) for r in dom.find(class_='tracking').find_all('tr')[1:]]


def parse_entry_row(row):
    return {['status', 'datetime', 'place'][i]: r.text.strip() for i, r in enumerate(row.find_all('td'))}


if __name__ == '__main__':
    app.run()
