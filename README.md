Author's notes:

- The Python script parse_tweets.py depends on apgl for graph support, which I have included with this git tree in the "src" directory. This graph implementation allows one to store values in edges, which I use to maintain state about how many unique tweets in the last 60 seconds have connected two vertices. This assists the program in knowing whether a 60 second window expiring merely causes the value to be decremented by one (if other tweets during that time also had the same hashtag pairs), or whether the edge gets removed (if the value goes to 0).

- The escape characters \t and \n will be removed from the tweets and replaced with spaces. You can easily modify which escape characters will be replaced by changing line 9 of the function process_tweets

- timestamp_ms tag has been used to get the time of each tweet, as opposed to using the created_at tag. I emailed cc@insightdataengineering.com and was told that this was okay.

- The arguments to the parse_tweets.py script are as follows (in case you wish to run it outside of the run.sh script):
    * -i <input file> (the file containing the JSON Twitter feed)
    * -f <output file for first feature>
    * -s <output file for second feature>

- I have obviously attempted to write this so that it does not consume unnecessary memory (load in the entire batch of tweets and process them from memory), as data streams can be very large. Instead, the program reads in the tweets line by line and maintains only the necessary state at each step to write the next line to its output files.

- I have attempted to make the code understandable so that it can be easily modified if necessary. If you have any questions, please email me.

- This was tested using python 2.7.3 on a Debian system