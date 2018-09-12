# Module 2 - Create a Cryptocurrency

# Importing the libraries
import datetime # for setting the timestamp of each block
import hashlib # contains hash functions
import json # for json files
from flask import Flask, jsonify, request # Postman is an http client. It is used to interact with the blockchain. Flask is a framework for creating web applications that are based on the use of a blockchain
import requests
from uuid import uuid4
from urllib.parse import urlparse

# Part 1 - Building a Blockchain
# Definition of Blockchain class
class Blockchain:
    
    # method that initializes an object
    def __init__(self):
        self.chain = [] # the chain containing the different blocks
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0') # creates the genesis block, the first block of the blockchain
        self.nodes = set()
    # method that creates and adds a block to the blockchain
    def create_block(self, proof, previous_hash):
        # we define a dictionary, in which we define a block with some information
         block = {'index': len(self.chain) + 1, 
                  'timestamp': str(datetime.datetime.now()),
                  'proof': proof,
                  'previous_hash': previous_hash,
                  'transactions': self.transactions}
         self.transactions = [] # empty the list of transactions
         self.chain.append(block) # adds the block to the blockchain
         return block
    
    # method that gets the last block of the chain
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        new_proof = 1 # trial and error approach. We use a counter 
        check_proof = False # used to check if new_proof is the right proof
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest() # get a hash in exadecimal format
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode() # transforms block dict in json string
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        # traversing the whole chain
        while block_index < len(chain):
            block = chain[block_index]
            # check if the previous hash of the current block is different from the hash of the previous block
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest() 
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True
    
    # method thar creates and add the transaction to the list
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender': sender,
                                  'receiver': receiver,
                                  'amount': amount})
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
    
    def add_node(self, address):
        parsed_url = urlparse(address) # function used to parse an address (URL in general)
        self.nodes.add(parsed_url.netloc) # netloc is the url including the port
    
    # consensus of protocol
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain') # get the chain of each node in the network
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False
    
# Part 2 - Mining our Blockchain
       
# Creating a Flask-based Web App
app = Flask(__name__)

# Creating an address for the node on Port 5000
node_address = str(uuid4()).replace('-', '')
    
# Creating a Blockchain
blockchain = Blockchain()

# Mining a new block
@app.route('/mine_block', methods=['GET']) # decorator
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender = node_address, receiver = 'Hadelin', amount = 1)
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'Congratulations, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']}
    return jsonify(response), 200

# Getting the full Blockchain
@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

# Checking if the Blockchain is valid
@app.route('/is_valid', methods=['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'All good. The Blockchain is valid.'}
    else:
        response = {'message': 'Houston, we have a problem. The Blockchain is not valid.'}
    return jsonify(response), 200

# Adding a new transaction to the Blockchain
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json = request.get_json() # get the json file resulting by the request made in Postman
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all (key in json for key in transaction_keys): # if all keys in transaction_keys are not present in json file keys then...
        return 'Some elements of the transaction are missing', 400 # bad request
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    response = {'message': f'This transaction will be added to Block {index}'}
    return jsonify(response), 201 # for something that is created

# Part 3 - Decentralizing our Blockchain

# Connecting new nodes
@app.route('/connect_node', methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes') # get the addresses of the new nodes
    if nodes is None:
        return 'No node', 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'All the nodes are now connected. The Davcoin Blockchain now contains the following nodes',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201

# Replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'The nodes had different chains so the chain was replaced by the longest one.',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'All good. The chain is the longest one.',
                    'actual_chain': blockchain.chain}
    return jsonify(response), 200

# Running the app
app.run(host = '0.0.0.0', port = 5000)

