from time import sleep

import requests
limitLeft = 500  # Although in theory some other code could be hitting the API, start with a presumption that we have all 500.

def __request_rate_limited(request_function):
    def limit_rate(*args, **kwargs):
        global limitLeft
        # if limitLeft < 500: # DEBUG LINE ONLY
        # Because we get our "actual rate limit" from API calls, it will never be 500 -- at most 499 -- in the wild.
        # print('API calls remaining before making call: ' + str(limitLeft)) # DEBUG LINE ONLY
        if limitLeft < 10:
            print('API calls remaining approaching zero (below ten); sleeping for 2 seconds to refresh.')
            sleep(2)
        response = request_function(*args, **kwargs)
        limitLeft = int(response.headers['x-ratelimit-remaining'])
        print('API calls remaining after making call: ' + str(limitLeft)) # DEBUG LINE ONLY
        return response

    return limit_rate

check_github_url = "https://api.github.com/repos/gjwgit/cars"
    # Attach __request_rate_limited() to "requests.get" and "requests.post"
requests.get = __request_rate_limited(requests.get)
requests.post = __request_rate_limited(requests.post)

ref = requests.get(check_github_url).json()
print("ref", ref)

