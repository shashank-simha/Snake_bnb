from colorama import Fore
from dateutil import parser
from datetime import date
import datetime
import sys

from infrastructure.switchlang import switch
import infrastructure.state as state
import services.data_services as svc
import program

def run():
    print(' ****************** Welcome host **************** ')
    print()

    show_commands()

    while True:
        action = get_action()

        with switch(action) as s:
            s.case('c', create_account)
            s.case('l', log_into_account)
            s.case('a', list_cages)
            s.case('r', register_cage)
            s.case('u', update_availability)
            s.case('v', view_bookings)
            s.case('m', lambda: 'change_mode')
            s.case('o', logout)
            s.case(['x', 'bye', 'exit', 'exit()'], exit_app)
            s.case('?', show_commands)
            s.case('', lambda: None)
            s.default(unknown_command)

        if action:
            print()

        if s.result == 'change_mode':
            return


def show_commands():
    print('What action would you like to take:')
    print('[C]reate an account')
    print('[L]ogin to your account')
    print('List c[A]ges')
    print('[R]egister a cage')
    print('[U]pdate cage availability')
    print('[V]iew your bookings')
    print('Change [M]ode (guest or host)')
    print('Log[O]ut')
    print('e[X]it app')
    print('[?] Help (this info)')
    print()


def create_account():
    print(' ****************** REGISTER **************** ')
    name = input('What is your name? ')
    email = input('What is your email? ').strip().lower()
    password = input('Enter the passphrase : ')
    confirm_password = input('Retype the passphrase : ')
    if (name.strip(' ')=='' or email.strip(' ')=='' or password.strip(' ')==''):
        error_msg(f"ERROR: All fields are required")
        return
    
    if (password!=confirm_password):
        error_msg(f"ERROR: Passphrases didn't match.")
        return
    
    old_account,msg = svc.find_account_by_email(email,password)
    if old_account:
        error_msg(f"ERROR: Account with email {email} already exists.")
        return
        
    state.active_account = svc.create_account(name, email, password)
    success_msg(f"Created new account with id {state.active_account.id}.")


def log_into_account():
    print(' ****************** LOGIN **************** ')

    email = input('What is your email? ').strip().lower()
    password = input('Enter the passphrase : ')
    account,msg = svc.find_account_by_email(email,password)

    if (msg==1):
        error_msg(f'Could not find account with email {email}.')
        return
    elif (msg==2):
        error_msg(f"Email and Passphrase didn't match.")
        return

    state.active_account = account
    success_msg('Logged in successfully.')


def register_cage():
    print(' ****************** REGISTER CAGE **************** ')

    if not state.active_account:
        error_msg('You must login first to register a cage.')
        return

    meters = input('How many square meters is the cage? ')
    carpeted = input("Is it carpeted [y, n]? ").lower().startswith('y')
    has_toys = input("Have snake toys [y, n]? ").lower().startswith('y')
    allow_dangerous = input("Can you host venomous snakes [y, n]? ").lower().startswith('y')
    name = input("Give your cage a name: ")
    price = input("How much are you charging?  ")
    
    if ((not meters)or(not price)):
        error_msg('Dimension and price are mandatory')
        return
    try:
        meters = float(meters)
        price = float(price)
    except ValueError:    
        error_msg('Invalid dimension or price')
        return
        
    if name:
        name =str(name)
   
    cage = svc.register_cage( state.active_account, name, allow_dangerous, has_toys, carpeted, meters, price)

    state.reload_account()
    success_msg(f'Registered new cage with id {cage.id}.')


def list_cages(suppress_header=False):
    if not suppress_header:
        print(' ******************     Your cages     **************** ')

    if not state.active_account:
        error_msg('You must login first to view your cages.')
        return
    
    cages = svc.find_cages_for_user(state.active_account)
    print(f"You have {len(cages)} cages.")
    for idx, c in enumerate(cages):
        print(Fore.LIGHTBLUE_EX + 'Cage no : '+str(idx+1) + Fore.WHITE)
        print(f'name : {c.name}')
        print(f'dimension : {c.square_meters} meters')
        print(f'Carpeted : {c.is_carpeted}')
        print(f'Toys : {c.has_toys}')
        print(f'Allow venomous snakes : {c.allow_dangerous_snakes}')
        print(f'Price : {c.price}')
        print('Availability : ')
        for a in c.availabilities:
            print('  * from {} to {} '.format(a.from_date.date(),a.to_date.date()))
        print('Bookings : {}'.format(len(c.bookings)))

def update_availability():
    print(' ****************** Add available date **************** ')
    
    if not state.active_account:
        error_msg("You must log in first to update availability")
        return
    
    list_cages(suppress_header=True)
    print()
    cage_number = input("Enter cage number: ")
    if not cage_number.strip():
        error_msg('Cancelled')
        print()
        return
    try:
        cage_number = int(cage_number)
    
        cages = svc.find_cages_for_user(state.active_account)
        selected_cage = cages[cage_number - 1]
    except:
        error_msg('Invalid cage number')
        print()
        return
        
    success_msg("Selected cage {}".format(selected_cage.name))
    
    try:
        start_date = parser.parse(input("Enter available date [yyyy-mm-dd]: "))
        days = int(input("How many days is this block of time? "))
    except:
        error_msg('Invalid inputs')
        print()
        return
        
    svc.add_available_date(selected_cage,start_date,days)

    success_msg(f'Date added to cage {selected_cage.name}.')


def view_bookings():
    print(' ****************** Your bookings **************** ')
    
    if not state.active_account:
        error_msg("You must log in first to view bookings")
        return
    
    cages = svc.find_cages_for_user(state.active_account)
    print(f"You have {len(cages)} cages.")
    for idx, c in enumerate(cages):
        print(Fore.LIGHTBLUE_EX + str(idx+1) +'. ' + Fore.WHITE + c.name +' has '+ str(len(c.bookings)) + ' bookings.')
    print()
    cage_number = input("Enter cage number: ")
    print()
    if not cage_number.strip():
        error_msg('Cancelled')
        print()
        return
    try:
        cage_number = int(cage_number)
        selected_cage = cages[cage_number - 1]
    except:
        error_msg('Invalid cage number')
        print()
        return
    success_msg("Selected cage {}".format(selected_cage.name))
    for b in selected_cage.bookings:
        print(' * Booked date: {}, from {} for {} days.'.format(
        datetime.date(b.booked_date.year, b.booked_date.month, b.booked_date.day),
        datetime.date(b.check_in_date.year, b.check_in_date.month, b.check_in_date.day),
        b.duration_in_days
        ))
    

def logout():
    program.run()

def exit_app():
    print()
    print('bye')
    sys.exit()


def get_action():
    text = '> '
    if state.active_account:
        text = f'{state.active_account.name}> '

    action = input(Fore.YELLOW + text + Fore.WHITE)
    return action.strip().lower()


def unknown_command():
    print("Sorry we didn't understand that command.")


def success_msg(text):
    print(Fore.LIGHTGREEN_EX + text + Fore.WHITE)


def error_msg(text):
    print(Fore.LIGHTRED_EX + text + Fore.WHITE)