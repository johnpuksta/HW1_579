import hashlib
import json
from fastecdsa import ecdsa, keys, curve, point


class ScroogeCoin(object):
    def __init__(self):
        self.private_key, self.public_key = keys.gen_keypair(
            curve.secp256k1)  # MUST USE secp256k1 curve from fastecdsa
        # create the address using public key, and bitwise operation, may need hex(value).hexdigest()
        self.address = self.hash(
            int("{}{}".format(self.public_key.x, self.public_key.y)))
        self.chain = []  # list of all the blocks
        self.current_transactions = []  # list of all the current transactions

    def create_coins(self, receivers: dict):
        """
        Scrooge adds value to some coins
        :param receivers: {account:amount, account:amount, ...}
        """

        tx = {
            "sender": self.address,  # address
            # coins that are created do not come from anywhere
            "location": {"block": -1, "tx": -1},
            "receivers": receivers,
        }
        tx["hash"] = self.hash(tx)  # hash of tx n
        tx["signature"] = self.sign(tx["hash"])  # signed hash of tx
        self.current_transactions.append(tx)

    def hash(self, blob):
        """
        Creates a SHA-256 hash of a Block
        :param block: Block
        """
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        # use json.dumps().encode() and specify the corrent parameters
        # use hashlib to hash the output of json.dumps()
        dump = json.dumps(blob, sort_keys=True).encode('utf-8')
        return hashlib.sha256(dump).hexdigest()

    def sign(self, hash_):
        # use fastecdsa library
        return ecdsa.sign(hash_, self.private_key, curve=curve.secp256k1, hashfunc=ecdsa.sha256)

    def get_user_tx_positions(self, address):
        """
        Scrooge adds value to some coins
        :param address: User.address
        :return: list of all transactions where address is funded
        [{"block":block_num, "tx":tx_num, "amount":amount}, ...]
        """
        funded_transactions = []

        for block in self.chain:
            tx_index = 0
            for old_tx in block["transactions"]:
                for funded, amount in old_tx["receivers"].items():
                    if (address == funded):
                        funded_transactions.append(
                            {"block": block["index"], "tx": tx_index, "amount": amount})
                tx_index += 1

        return funded_transactions

    def validate_spent(self, tx):
        sumRec = 0

        for receivers in tx["receivers"].items():
            sumRec += receivers[1]

        acct_total = self.show_user_balance(tx["sender"])

        return True if acct_total == sumRec else False

    def validate_funds(self, tx):
        total_val = 0
        rec_val = 0
        sent_from_address = 0
        for block in self.chain:
            if tx["sender"] == block["transactions"][0]["sender"]:
                for addresses in block["transactions"][0]["receivers"].items():
                    if addresses[0] in tx["receivers"]:
                        sent_from_address += addresses[1]
        for location in tx["locations"]:
            total_val += location["amount"]

        for receivers in tx["receivers"].items():
            rec_val += receivers[1]

        return True if total_val - sent_from_address >= rec_val else False

    def validate_consumed(self, tx, public_key):
        if (len(self.current_transactions) == 0):
            return False
        if (tx in self.current_transactions):
            return True
        for transaction in self.current_transactions:
            address = self.hash(
                int("{}{}".format(public_key.x, public_key.y)))
            if (address == transaction["sender"]):
                return True
        return False

    def validate_hash(self, tx):
        dummyHash = {
            "sender": tx["sender"],
            "locations": tx["locations"],
            "receivers": tx["receivers"]
        }
        return True if tx["hash"] == self.hash(dummyHash) else False

    def validate_tx(self, tx, public_key):
        """
        validates a single transaction

        :param tx = {
            "sender" : User.address,
                ## a list of locations of previous transactions
                ## look at
            "locations" : [{"block":block_num, "tx":tx_num, "amount":amount}, ...],
            "receivers" : {account:amount, account:amount, ...}
        }

        :param public_key: User.public_key

        :return: if tx is valid return tx
        """
        # Checks that the hash
        is_correct_hash = self.validate_hash(tx)
        if (is_correct_hash == False):
            print("Transaction has incorrect Hash")
            return -1

        # Checks if signature is correct
        is_signed = ecdsa.verify(
            tx["signature"], tx["hash"], public_key, curve.secp256k1)
        if (is_signed == False):
            print("Incorrect Signature")
            return -1

        # Checks if user has enough funds to send transaction
        is_funded = self.validate_funds(tx)
        if (is_funded == False):
            print("Transaction is not Funded")
            return -1

        # Checks if sender and reciever have same coins
        is_all_spent = self.validate_spent(tx)
        if (is_all_spent == False):
            print("Transaction does not spend all coins")
            return -1

        # Checks if prev trans has been mined and removed from curr trans list to prevent double spend
        consumed_previous = self.validate_consumed(tx, public_key)
        if (consumed_previous != False):
            print("Previous transaction is not consumed")
            return -1

        return tx

    def mine(self):
        """
        mines a new block onto the chain
        """
        """""
        block = {
            'previous_hash': # previous_hash,
            'index': # index,
            'transactions': # transactions,
        }
        # hash and sign the block
        tx["hash"] = # hash of block
        tx["signature"] = # signed hash of block

        return block
        """
        if (len(self.current_transactions) == 0):
            return 0

        for transaction in self.current_transactions:
            currTran = []
            currTran.append(transaction)

            block = {
                # previous_hash,
                'previous_hash': self.chain[-1:][0]["hash"] if any(self.chain) else "NA",
                'index': len(self.chain),  # index,
                'transactions': currTran,  # transactions,
            }
            # hash and sign the block
            block["hash"] = self.hash(block)  # hash of block
            block["signature"] = self.sign(
                block["hash"])  # signed hash of block
            self.chain.append(block)
        self.current_transactions = []
        return self.chain

    def add_tx(self, tx, public_key):
        """
        checks that tx is valid
        adds tx to current_transactions

        :param tx = {
            "sender" : User.address,
                ## a list of locations of previous transactions
                ## look at
            "locations" : [{"block":block_num, "tx":tx_num, "amount":amount}, ...],
            "receivers" : {account:amount, account:amount, ...}
        }

        :param public_key: User.public_key

        :return: True if the tx is added to current_transactions
        """
        if (self.validate_tx(tx, public_key) == tx):
            self.current_transactions.append(tx)
            return True
        return False

    def show_user_balance(self, address):
        """
        prints balance of address
        :param address: User.address
        """
        coins_received = 0
        coins_sent = 0

        for block in self.chain:
            if address != block["transactions"][0]["sender"]:
                for addresses in block["transactions"][0]["receivers"].items():
                    if addresses[0] == address:
                        coins_received += addresses[1]
            else:
                for addresses in block["transactions"][0]["receivers"].items():
                    if addresses[0] != address:
                        coins_sent += addresses[1]
        return coins_received - coins_sent

    def show_block(self, block_num):
        """
        prints out a single formated block
        :param block_num: index of the block to be printed
        """
        block = self.chain[block_num]
        print("---------------")
        print("Block index: {0}".format(block["index"]))
        print("Block previous hash: {0}".format(block["previous_hash"]))
        print("Block signature: {0}".format(block["signature"]))
        print("Transactions:")
        for transaction in block["transactions"]:
            for transaction_info in transaction.items():
                print("{0}:{1}".format(
                    transaction_info[0], transaction_info[1]))
        print("---------------")


class User(object):
    def __init__(self, Scrooge):
        self.private_key, self.public_key = keys.gen_keypair(
            curve.secp256k1)  # MUST USE secp256k1 curve from fastecdsa
        # create the address using public key, and bitwise operation, may need hex(value).hexdigest()
        self.address = self.hash(
            int("{}{}".format(self.public_key.x, self.public_key.y)))

    def hash(self, blob):
        """
        Creates a SHA-256 hash of a Block
        :param block: Block
        :return: the hash of the blob
        """
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        # use json.dumps().encode() and specify the corrent parameters
        # use hashlib to hash the output of json.dumps()
        dump = json.dumps(blob, sort_keys=True).encode('utf-8')
        return hashlib.sha256(dump).hexdigest()

    def sign(self, hash_):
        # use fastecdsa library
        return ecdsa.sign(hash_, self.private_key, curve.secp256k1)

    def send_tx(self, receivers, previous_tx_locations):
        """
        creates a TX to be sent
        :param receivers: {account:amount, account:amount, ...}
        :param previous_tx_locations
        """

        tx = {
            "sender": self.address,  # address,
            "locations": previous_tx_locations,
            "receivers": receivers
        }

        tx["hash"] = self.hash(tx)  # hash of tx n
        tx["signature"] = self.sign(tx["hash"])  # signed hash of tx

        return tx
