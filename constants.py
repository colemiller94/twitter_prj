from tweepy import API
from tweepy import Cursor
#from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy import RateLimitError
from secrets import *


acceptable_locs = {
    'AL':['al','alabama'],
    'AK':['ak','alaska'],
    'AZ':['az','arizona'],
    'AR':['ar','arkansas'],
    'CA':['ca','california'],
    'CO':['co','colorado'],
    'CT':['ct','connecticut'],
    'DE':['de','delaware'],
    'FL':['fl','florida'],
    'GA':['ga','georgia'],
    'HI':['hi','hawaii'],
    'ID':['id','idaho'],
    'IL':['il','illinois'],
    'IN':['in','indiana'],
    'IA':['ia','iowa'],
    'KS':['ks','kansas'],
    'KY':['ky','kentucky'],
    'LA':['la','louisiana'],
    'ME':['me','maine'],
    'MD':['md','maryland'],
    'MA':['ma','massachusetts'],
    'MI':['mi','michigan'],
    'MN':['mn','minnesota'],
    'MS':['ms','mississippi'],
    'MO':['mo','missouri'],
    'MT':['mt','montana'],
    'NE':['ne','nebraska'],
    'NV':['nv','nevada'],
    'NH':['nh','newhampshire'],
    'NJ':['nj','newjersey','jersey'],
    'NM':['nm','newmexico'],
    'NY':['ny','newyork','nyc'],
    'NC':['nc','northcarolina'],
    'ND':['nd','northdakota'],
    'OH':['oh','ohio'],
    'OK':['ok','oklahoma'],
    'OR':['or','oregon'],
    'PA':['pa','pennsylvania'],
    'RI':['ri','rhodeisland','rhode'],
    'SC':['sc','southcarolina'],
    'SD':['sd','southdakota'],
    'TN':['tn','tennessee'],
    'TX':['tx','texas'],
    'UT':['ut','utah'],
    'VT':['vt','vermont'],
    'VA':['va','virginia'],
    'WA':['wa','washington'],
    'WV':['wv','westvirginia'],
    'WI':['wi','wisconsin'],
    'WY':['wy','wyoming'],
}

#unpacking/melting above dictionary to list for direct access
acceptable_terms = []
for each in acceptable_locs.values():
    acceptable_terms.extend(each)

#setting up authorization
auth = OAuthHandler(consumer_token, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

# Creation of the actual interface, using authentication
api = API(auth)
api.wait_on_rate_limit = True
try:
    redirect_url = auth.get_authorization_url()
except tweepy.TweepError:
    print('Error! Failed to get request token.')
