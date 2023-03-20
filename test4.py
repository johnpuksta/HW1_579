from ScroogeClass import ScroogeCoin, User


def main():
    Scrooge = ScroogeCoin()
    users = [User(Scrooge) for i in range(10)]
    Scrooge.create_coins(
        {users[0].address: 10, users[1].address: 20, users[3].address: 50})
    Scrooge.mine()

    print("User 0 balance before transaction: {0}".format(
        Scrooge.show_user_balance(users[0].address)))
    print("User 1 balance before transaction: {0}".format(
        Scrooge.show_user_balance(users[1].address)))
    print("User 3 balance before transaction: {0}".format(
        Scrooge.show_user_balance(users[3].address)))

    Scrooge.show_block(0)

    first_tx = users[0].send_tx(
        {users[1].address: 2, users[0].address: 8}, Scrooge.get_user_tx_positions(users[0].address))
    Scrooge.add_tx(first_tx, users[0].public_key)
    second_tx = users[0].send_tx(
        {users[1].address: 3, users[0].address: 7}, Scrooge.get_user_tx_positions(users[0].address))
    Scrooge.add_tx(second_tx, users[0].public_key)
    Scrooge.mine()

    print("User 0 balance after first transaction: {0}".format(
        Scrooge.show_user_balance(users[0].address)))
    print("User 1 balance after first transaction: {0}".format(
        Scrooge.show_user_balance(users[1].address)))
    print("User 3 balance after first transaction: {0}".format(
        Scrooge.show_user_balance(users[3].address)))

    Scrooge.show_block(1)


if __name__ == '__main__':
    main()
