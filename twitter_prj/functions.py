from tweepy import API
from tweepy import Cursor
#from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
import plotly.plotly as py
import plotly.tools as tls
#from tweepy import Stream
#from tweepy import RateLimitError
from constants import *
import pandas as pd
import re

        ###________________API_FUNCTIONS_______________________###
def get_n_tweets_df(screen_name,n=10):
    """
    Takes twitter handle as string,
    Builds Pandas DF of n most recent tweets,
    returns dataframe with specified fields
    """
    tempdf = pd.DataFrame([tweet._json for tweet in Cursor(api.user_timeline, screen_name, include_rts=False).items(n)])
    tempdf['created_at']= pd.to_datetime(tempdf.created_at)

    wanted_keys = ['id','text','created_at','favorite_count','retweet_count']
    return tempdf[wanted_keys]

def get_retweeters_column(df,n=100):
    """
    Takes dataframe w/'id' column of twitter user ids
    adds a new column with dtype list for retweeter ids per tweet
    returns modified df
    """
    df['retweeter_ids'] = df['id'].map(lambda x: [userid for userid in Cursor(api.retweeters, x).items(n)])
    return df

def get_locations_by_id(listofuserids):
    """
    Takes list of user ids
    Returns list of locations associated with user ids
    """
    if listofuserids:
        users = api.lookup_users(listofuserids)
        return list(filter(None,[user._json['location'] for user in users]))
    else: return []


def get_retweeter_locs_column(df):
    """
    Maps get_locations_by_id on given dataframe with 'retweeter_ids' column
    """

    df['retweeter_geos'] = df['retweeter_ids'].map(lambda x: get_locations_by_id(x))
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
    string = re.sub(r'rhode[ ]','rhode',string)
    return string

def get_real_location(loc):
    """
    takes messy string of what should be a location
    looks for state name patterns defined in accepteable terms (in constants)
    returns two letter state code associated with state name
    """
    #normalizing input, seperating into list
    clean = state_name_collapser(loc.replace(',',' ').lower())
    clean_split = clean.split()

    #filtering for words that show up in our list of acceptable terms, defined in constants
    values = [word for word in clean_split if word in acceptable_terms]

    #return key (ex 'NY' for 'new york') if associated value is found in dropping_trash
    output = ''
    for each,lst in acceptable_locs.items():
         for item in lst:
                if item in values:
                    output += each
    #HACK ALERT: if more than 1 associated key found (ex: 'california new york'-->'CANY',
    # only returns 1 key (alphabetically)
    return output[:2]

def get_real_location2(loc):
    """
    takes messy string of what should be a location
    looks for state name patterns defined in accepteable terms (in constants)
    returns two letter state code associated with state name
    """
    #normalizing input, seperating into list
    clean = state_name_collapser(loc.replace(',',' '))
    clean_split = clean.split()
    clean_split_lower = clean.lower().split()

    for each,lst in acceptable_locs.items():
        if each in clean_split:
            return each if each != 'DC'
        for item in lst:
                if item in clean_split_lower:
                    return each if each != 'DC'
    #HACK ALERT: if more than 1 associated key found (ex: 'california new york'-->'CANY',
    # only returns 1 key (alphabetically)
    #return output[:2]

def locs_parser(lstoflocs):
    """
    applies get_real_location to list of locations
    """
    return list(filter(None,[get_real_location(name) for name in lstoflocs]))

def item_counter(lst):
    """
    takes list and returns dictionary of unique value counts
    """
    tempdic= dict.fromkeys(set(lst),0)
    for each in lst:
        tempdic[each] += 1
    return tempdic

def dict_srs_agg(srs):
    """
    takes series of item count dictionaries
    aggregates the counts
    returns as pandas series with index of keys and values of counts
    """
    tempdic= {}
    for dct in srs:
        for k,v in dct.items():
            if k in tempdic:
                tempdic[k] += v
            else:
                tempdic[k] = v
    return pd.Series(tempdic)

def add_pcts_to_srs(srs):
    """
    takes series of quantities
    coerces to dataframe
    adds column where values are percentages of total
    """
    newdf = pd.DataFrame({'counts':srs})
    newdf['pcts'] = newdf['counts'].apply(lambda x: round(x/newdf['counts'].sum()*100,2))
    return newdf.sort_index()



###________________HIGHER_LEVEL_FUNCTIONS_______________________###
def build_df_from_api(screen_name,n=10):
    """
    handles all api interactions
    takes string of twitter screen name
    retuns dataframe
    """
    #return n=10 tweets + column of lists of retweeter ids
    df = get_n_tweets_df(screen_name,n)
    #returns column of locations retweeters
    df = get_retweeters_column(df)
    df = get_retweeter_locs_column(df)
    #add column of cleaned up locations
    df['parsed_locs'] = df['retweeter_geos'].map(lambda x: locs_parser(x))
    #add column of location count as dictionary
    df['rt_loc_counts'] = df['parsed_locs'].map(lambda x: item_counter(x))
    df['screen_name'] = screen_name
    return df

def build_aggregation_df(df,on_series='rt_loc_counts',):
    """
    takes dataframe w/a column of value count dictionaries
    aggregates dictionaries
    creates new dataframe where rows are keys in the the aggregate dictionary
    return dataframe with additional columns for later processing
    """
    #collapse rows of dictionaries to summation series where each row is a dictionary key
    aggdic_srs = dict_srs_agg(df[on_series])
    #print(aggdic_srs)
    #adds percentage column which coerces to df
    newdf = add_pcts_to_srs(aggdic_srs)
    #adds copy of index as column to facilitate working with plotly]
    newdf['codes'] = newdf.index
    newdf['screen_name'] =df.loc[0]['screen_name']
    newdf['text'] = 'Count: '+newdf['counts'].astype(str)+' '+\
'Percentage: '+newdf['pcts'].astype(str)

    return newdf

def plotly_fig_compiler(df):
    name = df.screen_name[0]
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
        title = f'{name} RT Map',
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
    return py.iplot(plotly_fig_compiler(df), filename = title)
#____________________________________________


def fav_rt_histogram(dem1_df, dem2_df, dem3_df, dem4_df):

    names = [dem1_df.loc[0]['name'],dem2_df.loc[0]['name'],dem3_df.loc[0]['name'],dem4_df.loc[0]['name'],]

    ax1 = dem1_df[['favorite_count','retweet_count']].plot(kind='bar', title =f"{names[0]}", figsize=[10,6], legend=True, fontsize=12)
    ax1.set_xlabel("Tweet", fontsize=12)
    ax1.set_ylabel("Number", fontsize=12)

    ax2 = dem2_df[['favorite_count','retweet_count']].plot(kind='bar', title =f"{names[1]}", figsize=[10,6], legend=True, fontsize=12)
    ax2.set_xlabel("Tweet", fontsize=12)
    ax2.set_ylabel("Number", fontsize=12)

    ax3 = dem3_df[['favorite_count','retweet_count']].plot(kind='bar', title =f"{names[2]}", figsize=[10,6], legend=True, fontsize=12)
    ax3.set_xlabel( "Tweet", fontsize=12)
    ax3.set_ylabel("Number", fontsize=12)

    ax4 = dem4_df[['favorite_count','retweet_count']].plot(kind='bar', title =f"{names[3]}", figsize=[10,6], legend=True, fontsize=12)
    ax4.set_xlabel("Tweet", fontsize=12)
    ax4.set_ylabel("Number", fontsize=12)

def rt_histogram(dem1_df, dem2_df, dem3_df, dem4_df,tweet_index):
    names = [dem1_df.loc[0]['name'],dem2_df.loc[0]['name'],dem3_df.loc[0]['name'],dem4_df.loc[0]['name'],]

    rtdata = []
    for dem_df in [dem1_df, dem2_df, dem3_df, dem4_df]:
        rtdata.append(dem_df.loc[tweet_index]['rt_loc_counts'])

    new_figure = plt.figure(figsize=(20,16))


    # Add 4 subplots (2 side by side) to the figure - 4 new axes
    ax1 = new_figure.add_subplot(2,2,1)
    ax2 = new_figure.add_subplot(2,2,2)
    ax3 = new_figure.add_subplot(2,2,3)
    ax4 = new_figure.add_subplot(2,2,4)

    ax1.bar(rtdata[0].keys(), rtdata[0].values(), color='green')
    ax2.bar(rtdata[1].keys(), rtdata[1].values(), color='blue')
    ax3.bar(rtdata[2].keys(), rtdata[2].values(), color='orange')
    ax4.bar(rtdata[3].keys(), rtdata[3].values(), color='red')

    ax1.set_xlabel('US States')
    ax1.set_ylabel('Retweeter Count')
    ax1.set_title(f'{names[0]}')

    ax2.set_xlabel('US States')
    ax2.set_ylabel('Retweeter Count')
    ax2.set_title(f'{names[1]}')

    ax3.set_xlabel('US States')
    ax3.set_ylabel('Retweeter Count')
    ax3.set_title(f'{names[2]}')

    ax4.set_xlabel('US States')
    ax4.set_ylabel('Retweeter Count')
    ax4.set_title(f'{names[3]}')

    return new_figure
