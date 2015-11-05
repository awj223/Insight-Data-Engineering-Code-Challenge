import json
import re
import sys
import getopt
from apgl.graph import *
import Queue as Q

# Removes unicode from string str and then returns a string with
# the unicode gone
def remove_unicode(str):
   return re.sub(r'[^\x00-\x7F]','',str)

def evict_entries_from_graph(timestamp_ms, tweet_graph, time_queue):
    # Eviction cutoff time is 60 seconds before current tweet
    timestamp_evict = int(timestamp_ms) - 60000

    # Go through the queue and look for edges to evict from the graph
    while not time_queue.empty():
        edge_time = time_queue.get()
        
        # If next item is after eviction cutoff time, then there are no more items to evict
        if int(edge_time[0]) > timestamp_evict:

            # Put the item back into the priority queue for later, and break out of loop
            time_queue.put(edge_time)
            break

        # Item must be evicted from graph or its count decremented
        edgeValue = tweet_graph.getEdge(edge_time[1], edge_time[2])

        if edgeValue == 1:
            # The count was 1, so after decrementing, it will be 0. Delete the edge.
            tweet_graph.removeEdge(edge_time[1], edge_time[2])

            neighbors_1 = tweet_graph.neighbours(edge_time[1])
            neighbors_2 = tweet_graph.neighbours(edge_time[2])
            if neighbors_1 == []:
                tweet_graph.removeVertex(edge_time[1])
            if neighbors_2 == []:
                tweet_graph.removeVertex(edge_time[2])

        else:
            # Decrement the count on this edge. There must be some other tweet (in the future from this one)
            # which is keeping this edge in existence, for now.
            tweet_graph.addEdge(edge_time[1], edge_time[2], edgeValue - 1)

def process_hashtags_for_tweet(hashtags, timestamp_ms, tweet_graph, time_queue):
    hashtag_array = []
    # Process all hashtags for an incoming tweet. Add any necessary entries to graph.
    for hashtag in hashtags:
        hashtag_text = hashtag["text"]
        hashtag_array.append(hashtag_text)

        if len(hashtag_array) > 1:

            #Add any new edges and vertexes to the graph
            for i in range(0, len(hashtag_array)):
                for j in range(i+1, len(hashtag_array)):
                    hashtag1 = remove_unicode(hashtag_array[i].lower())
                    hashtag2 = remove_unicode(hashtag_array[j].lower())

                    # If, for some reason, a tweet has two identical hashtags, this does NOT generate an edge
                    if hashtag1 == hashtag2:
                        break

                    # Removing unicode from a hashtag can create an empty hashtag. If this happens to either tag,
                    # don't process this pair
                    if (len(hashtag1) == 0) or (len(hashtag2) == 0):
                        break

                    # If one of the two vertices does not exist, we have to create a new vertex, and a new edge,
                    # and set the edge value to 1.
                    if not(tweet_graph.vertexExists(hashtag1)) or not(tweet_graph.vertexExists(hashtag2)):
                        tweet_graph.addEdge(hashtag1, hashtag2, 1)

                    # If both vertices already exist...
                    else:
                        edgeValue = tweet_graph.getEdge(hashtag1, hashtag2)

                        if edgeValue is None:
                            # If there was NOT an edge between the two vertices, then create one, with value 1
                            tweet_graph.addEdge(hashtag1, hashtag2, 1)
                        else:
                            # If there was already an edge, then we need to increment its value by 1
                            tweet_graph.addEdge(hashtag1, hashtag2, edgeValue + 1)

                    # Add the timestamp to the queue
                    time_queue.put((timestamp_ms, hashtag1, hashtag2))

def process_tweets(inputfile, outputfile1, outputfile2):

    tweet_graph = DictGraph()
    time_queue = Q.PriorityQueue()

    unicode_tweets = 0
    #total_tweets = 0

    # These are the escape characters that must be removed from tweets
    escape_characters = re.compile(r'[\n\t]+')

    # Open the two files
    infile= open(inputfile, 'r')
    outfile1= open(outputfile1, 'w')
    outfile2= open(outputfile2, 'w')

    for line in infile:
        json_data = json.loads(line)

        # Take all tweets but ignore limit notices
        if 'created_at' in json_data:
 
            # Get timestamp and unsanitized text
            timestamp = json_data["created_at"]
 
            tweet_text = json_data["text"]
 
            # Find out if the tweet has unicode
            # Increment counter and remove unicode if it does
            try:
                tweet_text.decode("ascii")
            except UnicodeEncodeError:
                unicode_tweets += 1
                tweet_text = remove_unicode(tweet_text)
            else:
                pass

            # Remove the escape characters from the tweet
            tweet_text = re.sub(escape_characters, ' ', tweet_text)

            # Get timestamp and hashtags from tweet
            entities = json_data["entities"]
            timestamp_ms = json_data["timestamp_ms"]

            hashtags = entities["hashtags"]

            # Process all of the hashtags for this one specific tweet
            process_hashtags_for_tweet(hashtags, timestamp_ms, tweet_graph, time_queue)

            # Process timestamp of the tweet. This *may* evict entries from the graph.
            # Timestamp must be processed even if the tweet contains no hashtags.
            evict_entries_from_graph(timestamp_ms, tweet_graph, time_queue)
                
            # Write the tweet text and timestamp to first output file
            outfile1.write(tweet_text + " (timestamp: " + timestamp + ")\n")

            # Calculate average degree of the graph after every tweet and write to second file
            numEdges = tweet_graph.getNumEdges()
            numVertices = tweet_graph.getNumVertices()
            if numVertices == 0:
                avg_degree = 0
            else:
                avg_degree = float(2*numEdges)/numVertices

            outfile2.write("{0:.2f}".format(avg_degree))
            outfile2.write("\n")
        else:
            pass

    outfile1.write("\n")
    outfile1.write(repr(unicode_tweets) + " tweets contained unicode.")

    infile.close()
    outfile1.close()
    outfile2.close()

def main(argv):
    inputfile = ''
    outputfile1 = ''
    outputfile2 = ''
    try:
        opts, args = getopt.getopt(argv,"hi:f:s:",["ifile=","first=","second="])
    except getopt.GetoptError:
        print 'parse_tweets.py -i <inputfile> -f <outputfile1> -s <outputfile2>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'test.py -i <inputfile> -f <outputfile1> -s <outputfile2>'
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-f", "--first"):
            outputfile1 = arg
        elif opt in ("-s", "--second"):
            outputfile2 = arg
    print 'Input file is "', inputfile
    print 'Output file 1 is "', outputfile1
    print 'Output file 2 is "', outputfile2

    process_tweets(inputfile, outputfile1, outputfile2)

if __name__ == "__main__":
   main(sys.argv[1:])
