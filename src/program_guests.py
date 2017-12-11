from colorama import Fore
from dateutil import parser
from datetime import date
import datetime

from infrastructure.switchlang import switch
import program_hosts as hosts
import services.data_services as svc
from program_hosts import success_msg, error_msg
import infrastructure.state as state
import program

def run():
    print(' ****************** Welcome guest **************** ')
    print()

    show_commands()

    while True:
        action = hosts.get_action()

        with switch(action) as s:
            s.case('c', hosts.create_account)
            s.case('l', hosts.log_into_account)

            s.case('a', add_a_snake)
            s.case('y', view_your_snakes)
            s.case('b', book_a_cage)
            s.case('v', view_bookings)
            s.case('m', lambda: 'change_mode')
            s.case('o', hosts.logout)

            s.case('?', show_commands)
            s.case('', lambda: None)
            s.case(['x', 'bye', 'exit', 'exit()'], hosts.exit_app)

            s.default(hosts.unknown_command)

        state.reload_account()

        if action:
            print()

        if s.result == 'change_mode':
            return


def show_commands():
    print('What action would you like to take:')
    print('[C]reate an account')
    print('[L]ogin to your account')
    print('[B]ook a cage')
    print('[A]dd a snake')
    print('View [y]our snakes')
    print('[V]iew your bookings')
    print('[M]ain menu')
    print('Log[O]ut')
    print('e[X]it app')
    print('[?] Help (this info)')
    print()


def add_a_snake():
    print(' ****************** Add a snake **************** ')
    if not state.active_account:
        error_msg("You must log in first to add a snake")
        return
    
    name = str(input("What is your snake's name? "))
    if not (name.strip(' ')):
        error_msg('name cannot be empty')
        return
    
    length = input('How long is your snake (in meters)? ')
    if not length:
        error_msg('Length is mandatory')
        return
    try:
        length = float(length)
    except ValueError:    
        error_msg('Invalid length')
        return
    
    species = input("Species? ")
    if not (name.strip(' ')):
        error_msg('species cannot be empty')
        return
        
    not_venomous = input("Is your snake venomous [y]es, [n]o? ").lower().startswith('n')
    is_venomous = not not_venomous
    
    snake = svc.add_snake(state.active_account, name, length, species, is_venomous)
    state.reload_account()
    success_msg('Created {} with id {}'.format(snake.name, snake.id))


def view_your_snakes(suppress_header=False):
    if not suppress_header:
        print(' ****************** Your snakes **************** ')
    if not state.active_account:
        error_msg("You must log in first to view your snakes")
        return
    
    snakes = svc.get_snakes_for_user(state.active_account.id)
    print("You have {} snakes.".format(len(snakes)))
    for idx, s in enumerate(snakes):
        print(Fore.LIGHTBLUE_EX + 'Snake no : '+str(idx+1) + Fore.WHITE)
        print(f'name : {s.name}')
        print(f'species : {s.species}')
        print(f'length : {s.length}')
        print(f'Venomous? : {s.is_venomous}')


def book_a_cage():
    print(' ****************** Book a cage **************** ')
    if not state.active_account:
        error_msg("You must log in first to book a cage")
        return
    
    snakes = svc.get_snakes_for_user(state.active_account.id)
    if not snakes:
        error_msg('You must first [a]dd a snake before you can book a cage.')
        return
    
    print("Let's start by finding available cages.")
    try:
        checkin = parser.parse(input("Check-in date [yyyy-mm-dd]: "))
        checkout = parser.parse(input("Check-out date [yyyy-mm-dd]: "))
    except:
        error_msg('Invalid inputs')
        return
            
    checkout = checkout + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)        
    if checkin >= checkout:
        error_msg('Check in must be before check out')
        return
    
    print()
    view_your_snakes(suppress_header=True)
    print()
    
    try:
        snake = snakes[int(input('Which snake do you want to book (number)')) - 1]
    except:
        error_msg('Invalid inputs')
        return
        
    cages = svc.get_available_cages(checkin, checkout, snake)
    
    print("There are {} cages available in that time.".format(len(cages)))
    print()
    for idx, c in enumerate(cages):
        print(" {}. {} with {}sq.m at ${}/night. carpeted: {}, has toys: {}.".format(
            idx + 1,
            c.name,
            c.square_meters,
            c.price,
            'yes' if c.is_carpeted else 'no',
            'yes' if c.has_toys else 'no'))
    
    if not cages:
        error_msg("Sorry, no cages are available for that date.")
        return
    try:
   		cage = cages[int(input('Which cage do you want to book (number)')) - 1]
    except:
    	error_msg('Invalid inputs')
    	return
    
    svc.book_cage(state.active_account, snake, cage, checkin, checkout)
    
    success_msg('Successfully booked {} for {} at ${}/night.'.format(cage.name, snake.name, cage.price))


def view_bookings():
    print(' ****************** Your bookings **************** ')
    if not state.active_account:
        error_msg("You must log in first to view bookings")
        return

    snakes = {s.id: s for s in svc.get_snakes_for_user(state.active_account.id)}
    bookings = svc.get_bookings_for_user(state.active_account)
    print()
    print("You have {} bookings.".format(len(bookings)))
    for b in bookings:
        print(' * Snake: {} is booked at {} from {} for {} days.'.format(
            snakes.get(b.guest_snake_id).name,
            b.cage.name,
            datetime.date(b.check_in_date.year, b.check_in_date.month, b.check_in_date.day),
            (b.check_out_date - b.check_in_date + datetime.timedelta(seconds=1)).days
        ))