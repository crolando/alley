# usage: python osm_counter.py osm_file.osm output_file.txt
# This utility parses an OSM XML file, and outputs a text file that
# describes the most frequently used OSM tags and the most frequently
# used values for those tags.  This allows a developer wishing to use
# OSM data to scan a location for the most popular tags, and to see
# how the values are distributed.  

# In my case, I wanted to see what the mark-up tags on road lines 
# were, so I could prioritize what my road-building algorithms should
# look for.

# Please note this is my first python program, so it overuses dicts.
# Also note that this is a little hard to self-document because OSM
# uses string literals of "tag" and "k" (for key) and "v" (for value).
# which trust me is hard to document, as these are the names given
# to the dictionary members, which are used throughout.  

# library import
import xml.etree.ElementTree as et
import operator
import sys

# This is a little helper class that makes sorting all the tags easier at the end.
# I'm doing a 2d sort, so it gets pretty messy.
class counted_tag:
    def __init__(self,tag_name):
        self.tag_name = tag_name
        self.tag_count = 0
        self.unique_value_counts = {}

# These functions are for book keeping.  The idea was to have a dictionary where the
# key holds a tag, and the value is an integer, which describes how many tags were encountered.
def incr_dict_element(dic,key):
    if not key in dic:
        dic[key] = 1
    else:
        dic[key] = dic[key] + 1

# the primary data structure of this program is a dictionary of dictionaries.  
# dic holds "OSM Tag Names" as its key, and whose values are dicts where...
# the keys are "Values of that OSM Tag" and whose values are "the count of instances of that tag-value in the XML".
# This class helps me take this data structure, and intialize increment 
def incr_dict_k_v(dic,key,value):
    if not key in dic:
        dic[key] = {value:1}
    else:
        if not value in dic[key].keys():
            dic[key][value] = 1
        else:
            dic[key][value] = dic[key][value] + 1

# This is to me black magic.  I am pretty sure this just a boilerplate way to
# sort dictionaries based on an integer key, which to us is (see above):
# "the count of instances of that tag-value in the XML". 
# ultimately this sorting is required so the output has the highest counts at the top.
# https://stackoverflow.com/questions/613183/how-do-i-sort-a-dictionary-by-value
def sort_my_dict(dic):    
    return sorted(dic.items(),key=operator.itemgetter(1),reverse=True)

# This is really the guts of the program.  It takes a XML tree typical of OSM style, which
# marks up its data with "tag" node, with fields K and V, which store the attribute name and value 
# respectively.  Like this (raw XML incoming):
#    <tag k="highway" v="traffic_signals"/>
# So the whole point of the program is to count the number of instances of keys, then count the number
# of unique values within that key, then sort and print the report.  
# You'll find that since this is geared toward OSM, we hard code the element name "tag", and "k" and "v" below.
def print_element_counts(dic, element_type):
    print("===========================",element_type,"==============================",file=f)
    # Assemble Dict of countable_tag classes
    # Key = Tagname
    # Value = countable_tag
    countable_tag_dict = {}
    
    # This takes in the dictionary of ID->xml_elements, and builds up the countable_tag_dicts
	# for every ID (Aka every osm primitive)
    for node_id in dic:
		# get the xml out of the ID->xml dict
        xml_node = dic[node_id]
		# The xml has a lot of nodes, and we want to parse through the ones called "tag"
        for xml_tag in xml_node.iter('tag'):
            tag_name = xml_tag.get('k')
            tag_value = xml_tag.get('v')
			# At this point, we can increment our tag-counter and value-counter.
			# This guard of course adds the new tag if it's not there yet, because you can't
			# increment a dict key if it doesn't exist!
            if not tag_name in countable_tag_dict:
                countable_tag_dict[tag_name] = counted_tag(tag_name)
			# At this point, the class is guaranteed to have a count because of the class constructor.
			# This lets us freely increment the tag count.
            ct = countable_tag_dict[tag_name]
            ct.tag_count = ct.tag_count + 1
			
			# Next we do pretty much the same thing with the tag values.  First we get the dictionary
			# of the value->counts
            uvc = ct.unique_value_counts
			# Next we guard to make sure there's an initial entry to increment
            if not tag_value in uvc:
                uvc[tag_value] = 0
			# finally, we're guaranteed to have a counter for this value, so we increment the count
			# which is the value of the dictionary.
            uvc[tag_value] = uvc[tag_value] + 1
    
	# OK, so now we have a complete count of every tag, and every value within that tag, but they're
	# not sorted, which makes reading the text file really annoying.  So, we sort them.  This is a little
	# goofy because we have 2 layers of sorting to:  Keys, a category, and Values, the items in the category.
    # Also, doing this to dicts is too complicated, so I first stick the countable objects into a list, so it can
	# go through the "sorted" function.  Yes, I know I didn't have to do this.
    unsorted_list = []
    for elem in countable_tag_dict:
        unsorted_list.append(countable_tag_dict[elem])    
	# Then do some stack exchange black magic to sort the list.  Each list element is an object, where the "count"
	# is stored as a field.  So we need to store the classes based on their fields.  This is actually kind of a complicated
	# CS problem, but of course python is cool and can do it no problem.
    sorted_list = sorted(unsorted_list,key=operator.attrgetter('tag_count'),reverse=True)    

    # So at this point we have the categories sorted, but their child values are not sorted (again, they're just a dict)
	# so we call my function, which sort of does the same thing as above.  it returns an ordered list.
    for ct in sorted_list:
        sorted_uvcs = sort_my_dict(ct.unique_value_counts)
		# I found that we have a shit ton of "onesies" values, so we don't print those.  Since these are ordered,
		# once you hit a onesie, you KNOW that the rest are also onesies, and we use "break" to go to the next
		# category (tag key).
        if ct.tag_count > 1:
            print(ct.tag_count, ct.tag_name,file=f)
        else:
            print("X Skipping remaining singletons",file=f)
            break
        for uv in sorted_uvcs:
            if uv[1] > 1:
                print("  ",uv[1],uv[0],file=f)
            else:
                print("   X Skipping remaining singletons",file=f)
                break

# This is where we sorta start the program in earnest.  First, we do argument parsing...
# argument processing
if len(sys.argv)!= 3:
    print("Usage: osm_counter.py osm_file.osm output_file.txt")
    quit()

# Parse the XMl tree
print("attempting to parse first argument")
tree = et.parse(sys.argv[1])

# Open the output file
print("attempting to open second argument")
f = open(sys.argv[2],"w")
print("files opened OK, running...")

# setup hash tables that store all the OSM stuff.
# these hash tables use the OSM Integer ID as the key, then point to an XML element, which has all the OSM data.
root = tree.getroot()
nodes = {}
ways = {}
relations = {}
bounds = None

# This builds hash tables for all the OSM primitives.  This probably could be turned into simple arrays
# for this application, but this is experimental code.  OSM uses ID numbers for all cross-referencing,
# so having these makes for more useful code for future experiments which would require fast ID look-up.
for element in root:
    if element.tag == 'node':
        nodes[int(element.get('id'))] = element
    elif element.tag == 'way':
        ways[int(element.get('id'))] = element
    elif element.tag == 'relation':
        relations[int(element.get('id'))] = element
    elif element.tag == 'bounds':
        bounds = element
    else:
        print("Found unused element called: " + element.tag)				
				
# do the work
print_element_counts(nodes,"nodes")
print_element_counts(ways,"ways")
print_element_counts(relations,"relations")                     
print("finished")
