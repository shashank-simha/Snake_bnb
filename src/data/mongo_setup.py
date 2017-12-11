import mongoengine
import infrastructure.state as state

def global_init(): 
    state.active_account = None
    mongoengine.register_connection(alias='core',name='snake_bnb',host='localhost',port=8088)