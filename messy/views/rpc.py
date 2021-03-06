
from rhombus.lib.utils import random_string, get_dbhandler

import time

# User token management
#
# how to test token via curl
# curl -X POST -H 'Content-Type: application/json' \
# -d '{"jsonrpc":"2.0","id":234,"method":"check_auth","params":["utkn:YPGIt0lFw4HiN7vLaStOdWQXBGCiph_n"]}' \
# http://localhost:6543/rpc | python3 -m json.tool


def generate_user_token(request):

    token = 'utkn:' + random_string(32)
    payload = {'create_time': time.time(), 'userinstance': request.user}
    request.get_ticket(payload, token)
    return token


def get_userinstance_by_token(request, token):
    """ return user, errmsg """

    try:
        payload = request.get_data(token, 12 * 3600)
    except KeyError:
        return None, "token does not exist or is already expired"
    if (time.time() - payload['create_time']) / 3600 > 12:
        return None, "token is expired"
    return payload['userinstance'], ''


# public functions

def check_auth(request, token):

    userinstance, errmsg = get_userinstance_by_token(request, token)
    if userinstance is None:
        return {'auth': False, 'user': None, 'errmsg': errmsg}
    return {'auth': True, 'user': userinstance.login, 'errmsg': None}


def pipeline_upload(request, token, run_code, sample_code, data):

    userinstance, errmsg = get_userinstance_by_token(request, token)
    if userinstance is None:
        return {'auth': False, 'user': None, 'errmsg': errmsg}

    dbh = get_dbhandler()

    # parse incoming request
    # https://github.com/trmznt/ncov19-pipeline sends the following dictionary

    # either get the Sequence or create a new Sequence

    try:
        sq = dbh.get_sequences(
            groups=None,
            specs=[{'run_code': run_code, 'sample_code': sample_code}],
            user=userinstance,
            raise_if_empty=True
        )

    except dbh.NoResultFound:
        sq = dbh.Sequence(
            sequencingrun=run_code,
            sample=sample_code
        )
        dbh.session().add(sq)

    sq.update(data)

# EOF
