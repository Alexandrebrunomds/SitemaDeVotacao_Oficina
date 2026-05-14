from flask import Flask, render_template, request, redirect, url_for, flash

from blockchain.chain import Blockchain

import hashlib
import time
import logging

from logging.handlers import RotatingFileHandler

from datetime import datetime

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa


# =========================
# LOGGING
# =========================


def setup_logging():

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )

    file_handler = RotatingFileHandler(
        'blockchain.log',
        maxBytes=1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )

    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()

    root_logger.setLevel(logging.INFO)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


setup_logging()

logger = logging.getLogger(__name__)


# =========================
# FLASK
# =========================

app = Flask(__name__)

app.secret_key = 'blockchain_secret_key'


@app.template_filter('datetimeformat')
def datetimeformat(value, format='%d/%m/%Y %H:%M:%S'):

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value).strftime(format)

    return value


# =========================
# BLOCKCHAIN
# =========================

blockchain = Blockchain()


# =========================
# RSA KEYS
# =========================

private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

public_key = private_key.public_key()


# =========================
# SIGNATURE
# =========================


def sign_transaction(data):

    signature = private_key.sign(
        data.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    return signature.hex()


# =========================
# ROUTES
# =========================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/verify', methods=['POST'])
def verify():

    cpf = request.form['cpf']

    cpf = cpf.replace('.', '').replace('-', '')

    if len(cpf) != 11 or not cpf.isdigit():

        flash('CPF inválido.', 'error')

        return redirect(url_for('index'))

    cpf_hash = hashlib.sha256(cpf.encode()).hexdigest()

    for block in blockchain.chain:

        for tx in block.transactions:

            if tx.get('cpf_hash') == cpf_hash:

                flash('Este CPF já votou.', 'error')

                return redirect(url_for('index'))

    voter = {
        'cpf': cpf,
        'name': 'Eleitor'
    }

    return render_template('vote.html', voter=voter)


@app.route('/vote', methods=['POST'])
def vote():

    cpf = request.form['cpf']

    candidate_id = int(request.form['candidate'])

    cpf_hash = hashlib.sha256(cpf.encode()).hexdigest()

    transaction = {
        'type': 'vote',
        'cpf_hash': cpf_hash,
        'candidate_id': candidate_id,
        'timestamp': time.time()
    }

    transaction['signature'] = sign_transaction(str(transaction))

    blockchain.add_new_transaction(transaction)

    blockchain.mine()

    flash('Voto registrado com sucesso!', 'success')

    return redirect(url_for('index'))


@app.route('/results')
def results():

    votes = {}

    candidates = {
        1: {
            'name': 'Marcela',
            'party': 'Chapa 1'
        },
        2: {
            'name': 'Sergio',
            'party': 'Chapa 2'
        },
        3: {
            'name': 'Oswaldo',
            'party': 'Chapa 3'
        }
    }

    for block in blockchain.chain:

        for tx in block.transactions:

            if tx.get('type') == 'vote':

                candidate_id = tx['candidate_id']

                votes[candidate_id] = votes.get(candidate_id, 0) + 1

    results_data = []

    for candidate_id, candidate in candidates.items():

        results_data.append({
            'name': candidate['name'],
            'party': candidate['party'],
            'votes': votes.get(candidate_id, 0)
        })

    return render_template(
        'results.html',
        candidates=results_data
    )


@app.route('/blocks')
def blocks():

    return render_template(
        'blocks.html',
        blocks=blockchain.chain
    )


@app.route('/validate')
def validate_chain():

    valid = blockchain.check_chain_validity()

    if valid:
        return 'Blockchain válida.'

    return 'Blockchain inválida.'


if __name__ == '__main__':

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )