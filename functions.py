from tweepy import API
from tweepy import Cursor
#from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy import RateLimitError
from constants import *
import pandas as pd
import re

###________________API_FUNCTIONS_______________________###
def get_n_tweets_df(screen_name,n=10):
    wanted_status_keys = ['id','text','created_at','favorite_count','retweet_count','retweeter_ids','entities']
    temp = pd.DataFrame([tweet._json for tweet in Cursor(api.user_timeline, screen_name, include_rts=False).items(n)])
    temp['retweeter_ids'] = temp['id'].map(lambda x:api.retweeters(x))
    return temp[wanted_status_keys]

def get_location_by_id(idnum):
    return api.get_user(idnum)._json['location']

def add_retweet_geos(df):
    df['retweeter_geos'] = df['retweeter_ids'].map(lambda x: [get_location_by_id(idnum) for idnum in x])
    return df


###________________OFFLINE_FUNCTIONS_______________________###

def state_name_collapser(string):
    """
    eliminates space after given keywords
    """
    string = re.sub(r'north[ ]','north',string)
    string = re.sub(r'south[ ]','south',string)
    string = re.sub(r'west[ ]','west',string)
    string = re.sub(r'new[ ]','new',string)
    return string

def get_real_location(loc):
    #normalizing input, seperating into list
    clean = state_name_collapser(loc.replace(',','').lower())
    clean_split = clean.split()

    #filtering for words that show up in our list of acceptable terms
    dropping_trash = [word for word in clean_split if word in acceptable_terms]

    #return key (ex 'NY' for 'new york') if associated value is found in dropping_trash
    output = ''
    for each,lst in acceptable_locs.items():
         for item in lst:
                if item in dropping_trash:
                    output += each
    #HACK ALERT: if more than 1 associated key found (ex: 'california new york'-->'CANY', only returns 1 key (alphabetically)
    return output[:2]

def locs_parser(lstoflocs):
    return list(filter(None,[get_real_location(name) for name in lstoflocs]))

def item_counter(lst):
    tempdic={}
    for each in lst:
        if each in tempdic:
            tempdic[each] += 1
        else:
            tempdic[each] = 1
    return tempdic

def dict_srs_agg(srs):
    tempdic= {}
    for dct in srs:
       # print(dct)
        for k,v in dct.items():
           # print(k,v)
            if k in tempdic:
                tempdic[k] += v
            else:
                tempdic[k] = v
    return pd.Series(tempdic)

def add_pcts_to_srs(srs):
    newdf = pd.DataFrame({'counts':srs})
    newdf['pcts'] = newdf['counts'].apply(lambda x: round(x/newdf['counts'].sum()*100,2))
    return newdf.sort_index()



###________________HIGHER_LEVEL_FUNCTIONS_______________________###
def build_df_from_api(screen_name):
    #return n=10 tweets + column of lists of retweeter ids
    df = get_n_tweets_df(screen_name)
    #returns user defined locations of retweeters
    df = add_retweet_geos(df)
    #add column of cleaned up locations
    df['parsed_locs'] = df['retweeter_geos'].map(lambda x: locs_parser(x))
    #add column of location count as dictionary
    df['rt_loc_counts'] = df['parsed_locs'].map(lambda x: item_counter(x))
    return df

def build_aggregation_df(df):
    #collapse rows of dictionaries to summation series where each row is a dictionary key
    aggdic_srs = dict_srs_agg(df['rt_loc_counts'])
    #print(aggdic_srs)
    #adds percentage column which coerces to df
    newdf = add_pcts_to_srs(aggdic_srs)
    #adds copy of index as column to facilitate working with plotly
    newdf['codes'] = newdf.index
    newdf['text'] = 'Count: '+newdf['counts'].astype(str)+' '+\
'Percentage: '+newdf['pcts'].astype(str)
    return newdf

def plotly_compiler(df):
    data = [dict(
        type='choropleth',
        autocolorscale = True,
        locations = df['codes'],
        z = df['counts'].astype(float),
        locationmode = 'USA-states',
        text = df['text'],
        marker = dict(
            line = dict (
                color = 'rgb(255,255,255)',
                width = 2))
    )]
    layout = dict(
        title = 'RT Map',
        geo = dict(
            scope='usa',
            projection = dict(type = 'albers usa'),
            showlakes = True,
            lakecolor = 'rgb(255, 255, 255)'
        )
    )
    fig = dict(data = data, layout=layout)
    return fig

def plotly_plot(df,title):
    return py.iplot(plotly_compiler(df), filename = title)
