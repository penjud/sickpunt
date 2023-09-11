"""Connection routines"""

import betfairlightweight

APP_KEY = "mECg2P2ohk92MLXy"
PASSWORD = r"%2s8ThBv&u5#s$Wg"
USERNAME = "penjud"

client = betfairlightweight.APIClient(
    username=USERNAME, password=PASSWORD, app_key=APP_KEY)
client.login_interactive()
