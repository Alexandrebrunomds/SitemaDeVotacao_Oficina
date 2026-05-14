import json
import os
import time
import logging
from blockchain.block import Block

logger = logging.getLogger(__name__)


class Blockchain:

    difficulty = 3

    def __init__(self):
        self.chain = []
        self.unconfirmed_transactions = []

        self.load_chain()

        if not self.chain:
            self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(
            index=0,
            transactions=[],
            timestamp=time.time(),
            previous_hash='0'
        )

        genesis_block.hash = genesis_block.compute_hash()

        self.chain.append(genesis_block)
        self.save_chain()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, block):
        block.nonce = 0

        computed_hash = block.compute_hash()

        while not computed_hash.startswith('0' * self.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def is_valid_proof(self, block, block_hash):
        return (
            block_hash.startswith('0' * self.difficulty)
            and block_hash == block.compute_hash()
        )

    def add_block(self, block, proof):

        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False

        if not self.is_valid_proof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)

        self.save_chain()

        return True

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)
        self.save_chain()

    def mine(self):

        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block

        new_block = Block(
            index=last_block.index + 1,
            transactions=self.unconfirmed_transactions,
            timestamp=time.time(),
            previous_hash=last_block.hash
        )

        proof = self.proof_of_work(new_block)

        self.add_block(new_block, proof)

        self.unconfirmed_transactions = []

        self.save_chain()

        return new_block.index

    def save_chain(self):

        data = {
            'chain': [block.__dict__ for block in self.chain],
            'pending_tx': self.unconfirmed_transactions
        }

        with open('blockchain_data.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)

    def load_chain(self):

        if not os.path.exists('blockchain_data.json'):
            return

        with open('blockchain_data.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

        self.chain = []

        for block_data in data['chain']:

            block = Block(
                index=block_data['index'],
                transactions=block_data['transactions'],
                timestamp=block_data['timestamp'],
                previous_hash=block_data['previous_hash'],
                nonce=block_data['nonce']
            )

            block.hash = block_data['hash']

            self.chain.append(block)

        self.unconfirmed_transactions = data.get('pending_tx', [])

    def check_chain_validity(self):

        previous_hash = '0'

        for block in self.chain:

            block_hash = block.hash

            if block.index != 0:

                if not self.is_valid_proof(block, block_hash):
                    return False

                if previous_hash != block.previous_hash:
                    return False

            previous_hash = block_hash

        return True