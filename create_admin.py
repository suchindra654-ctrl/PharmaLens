from getpass import getpass
from accounts import Accounts

if __name__ == '__main__':
    print('Create the first PharmaLens administrator (local demo).')
    username = input('Username: ')
    name = input('Display name: ')
    password = getpass('Password (12+ characters): ')
    if password != getpass('Repeat password: '):
        raise SystemExit('Passwords do not match. No account created.')
    try:
        Accounts().bootstrap(username, password, name)
        print('Administrator created. Start the app and sign in.')
    except ValueError as error:
        raise SystemExit(str(error))
