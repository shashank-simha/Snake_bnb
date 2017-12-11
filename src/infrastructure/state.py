import services.data_services as svc

active_account = None


def reload_account():
    global active_account
    if not active_account:
        return

    active_account,msg = svc.find_account_by_email(active_account.email,active_account.password)