from typing import List

import datetime

import bson
from data.bookings import Booking
from data.availabilities import Availability
from data.cages import Cage
from data.owners import Owner
from data.snakes import Snake


def create_account(name: str, email: str, password: str) -> Owner:
    owner = Owner()
    owner.name = name
    owner.email = email
    owner.password = password

    owner.save()

    return owner


def find_account_by_email(email: str, password: str) -> Owner:
    owner = Owner.objects(email=email).first()
    msg=0
    
    if not owner:
        msg=1
    elif (owner.password!=password):
        msg=2
        
    return owner,msg
    
def register_cage(active_account: Owner, name:str, allow_dangerous:bool, has_toys:bool, carpeted:bool, meters:float, price:float) -> Cage:
    cage = Cage()

    cage.name = name
    cage.square_meters = meters
    cage.is_carpeted = carpeted
    cage.has_toys = has_toys
    cage.allow_dangerous_snakes = allow_dangerous
    cage.price = price

    cage.save()

    account,msg = find_account_by_email(active_account.email, active_account.password)
    account.cage_ids.append(cage.id)
    account.save()

    return cage

def find_cages_for_user(account: Owner) -> List[Cage]:
    query = Cage.objects(id__in=account.cage_ids)
    cages = list(query)

    return cages

def add_available_date(cage: Cage,start_date: datetime.datetime, days: int) -> Cage:
                       
    availability = Availability()
    availability.from_date = start_date
    availability.to_date = start_date + datetime.timedelta(days=days) - datetime.timedelta(seconds=1)
    
    cage = Cage.objects(id=cage.id).first()
    try:
        cage.availabilities[0] = availability
    except:
        cage.availabilities.append(availability)
        
    cage.save()

    return cage
    
def add_snake(account:Owner, name:str, length:float, species:str, is_venomous:bool) -> Snake:
    snake = Snake()
    snake.name = name
    snake.length = length
    snake.species = species
    snake.is_venomous = is_venomous
    snake.save()

    owner,msg = find_account_by_email(account.email, account.password)
    owner.snake_ids.append(snake.id)
    owner.save()

    return snake


def get_snakes_for_user(user_id: bson.ObjectId) -> List[Snake]:
    owner = Owner.objects(id=user_id).first()
    query = Snake.objects(id__in=owner.snake_ids).all()
    snakes = list(query)

    return snakes
    
def get_snakes_for_user(user_id: bson.ObjectId) -> List[Snake]:
    owner = Owner.objects(id=user_id).first()
    snakes = Snake.objects(id__in=owner.snake_ids).all()

    return list(snakes)


def get_available_cages(checkin: datetime.datetime, checkout: datetime.datetime, snake: Snake) -> List[Cage]:
    min_size = snake.length / 4
    
    query = Cage.objects() \
        .filter(square_meters__gte=min_size) \
        .filter(availabilities__from_date__lte=checkin) \
        .filter(availabilities__to_date__gte=checkout)

    if snake.is_venomous:
        query = query.filter(allow_dangerous_snakes=True)

    cages = query.order_by('price', '-square_meters')

    final_cages = []
    for c in cages:
        booked=0
        for b in c.bookings:
            if ((b.check_in_date <= checkin and b.check_out_date >= checkin) or (b.check_in_date <= checkout and b.check_out_date >= checkout)):
                booked+=1
                break
                
        if (booked==0):
            final_cages.append(c)
            
    return final_cages
    
def book_cage(account:Owner, snake:Snake, cage:Cage, checkin:datetime.datetime, checkout:datetime.datetime):
    booking = Booking()
    
    booking.guest_owner_id = account.id
    booking.guest_snake_id = snake.id
    booking.booked_date = datetime.datetime.now()
    booking.check_in_date = checkin
    booking.check_out_date = checkout
    
    cage = Cage.objects(id=cage.id).first()
    cage.bookings.append(booking)
    
    cage.save()
    
def get_bookings_for_user(account:Owner) -> List[Booking]:

    booked_cages = Cage.objects() \
        .filter(bookings__guest_owner_id=account.id) \
        .only('bookings', 'name')

    def map_cage_to_booking(cage, booking):
        booking.cage = cage
        return booking

    bookings = [
        map_cage_to_booking(cage, booking)
        for cage in booked_cages
        for booking in cage.bookings
        if booking.guest_owner_id == account.id
    ]

    return bookings