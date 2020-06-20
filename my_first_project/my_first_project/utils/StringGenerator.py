import random
import string

def randomString(stringLength=4):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(stringLength))


def randomNumber(stringLength=6):
    letters = string.digits
    return ''.join(random.choice(letters) for i in range(stringLength))

